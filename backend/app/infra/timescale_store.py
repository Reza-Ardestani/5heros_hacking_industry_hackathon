"""Timescale read adapter and ordered, restart-safe SQLite replication."""

import re
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from itertools import groupby
from zoneinfo import ZoneInfo

import psycopg
from psycopg import sql

from app.infra.sqlite_store import SCHEMA, SQLiteStore, utc_now

PG_SCHEMA = "bottleneck_busters"
TRAVEL_SCHEMA = """
CREATE TABLE IF NOT EXISTS travel_time_samples (
  segment TEXT NOT NULL, corridor TEXT, city_updated_local TEXT NOT NULL,
  travel_time_min DOUBLE PRECISION, fetched_utc TEXT NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (segment, city_updated_local, observed_at)
);
CREATE OR REPLACE VIEW travel_time_obs AS
  SELECT segment, corridor, city_updated_local, travel_time_min, fetched_utc
  FROM travel_time_samples;
CREATE OR REPLACE VIEW sim_trials AS
  SELECT run_id, alt_id, purpose, seed, demand_factor, demand_sha256,
         network_sha256, metrics_json, condition FROM simulation_trial_rows;
"""
REPLICA_SCHEMA = """
CREATE TABLE IF NOT EXISTS replica_state (
  singleton INTEGER PRIMARY KEY CHECK(singleton=1), source_id TEXT NOT NULL,
  applied_seq BIGINT NOT NULL DEFAULT 0, last_sync_utc TIMESTAMPTZ
);
"""


class SourceMismatch(RuntimeError):
    """Independent SQLite histories must never share a mirror."""


class HybridRow:
    """The existing store reads rows by column name and integer position."""

    def __init__(self, columns, values):
        self.values = values
        self.mapping = dict(zip(columns, values, strict=True))

    def keys(self):
        return self.mapping.keys()

    def __getitem__(self, key):
        return self.values[key] if isinstance(key, int) else self.mapping[key]

    def __iter__(self):
        return iter(self.values)


def hybrid_rows(cursor):
    columns = [c.name for c in cursor.description] if cursor.description else []
    return lambda values: HybridRow(columns, values)


class ReadConnection:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, params=()):
        if not query.lstrip().upper().startswith("SELECT"):
            raise ValueError("Timescale read adapter accepts SELECT only")
        return self.connection.execute(query.replace("%", "%%").replace("?", "%s"), params)


class TimescaleReadStore(SQLiteStore):
    def __init__(self, mirror, path):
        self.mirror, self.path = mirror, path

    @contextmanager
    def connect(self):
        with self.mirror.connection(row_factory=hybrid_rows) as db:
            db.execute("SET TRANSACTION READ ONLY")
            yield ReadConnection(db)

    def display_path(self):
        return "timescaledb/bottleneck_busters"

    def stats(self):
        result = super().stats()
        with self.connect() as db:
            result["db_bytes"] = int(db.execute(
                "SELECT pg_database_size(current_database())"
            ).fetchone()[0])
        result["db_bytes_scope"] = "whole_postgresql_database"
        return result


class TimescaleMirror:
    def __init__(self, url, journal, retry_seconds=5, batch_size=1000, clock=time.monotonic):
        self._url, self.journal = url, journal
        self.retry_seconds, self.batch_size, self.clock = retry_seconds, batch_size, clock
        self._lock = threading.Lock()
        self._schema_ready = False
        self._failures, self._retry_at = 0, 0.0
        self.last_error = None
        self.healthy = False

    @contextmanager
    def connection(self, **kwargs):
        with psycopg.connect(
            self._url, connect_timeout=2,
            options="-c statement_timeout=5000 -c lock_timeout=2000",
            **kwargs,
        ) as db:
            db.execute("SET search_path TO bottleneck_busters, public")
            yield db

    def failed(self, error):
        self.healthy = False
        if isinstance(error, (psycopg.errors.UndefinedTable, psycopg.errors.InvalidSchemaName)):
            self._schema_ready = False
        self._failures += 1
        # Raw exceptions may contain credentials or server connection details.
        self.last_error = (
            "source_mismatch" if isinstance(error, SourceMismatch)
            else "local_ack_failed" if isinstance(error, sqlite3.Error)
            else "invalid_replication_data" if isinstance(error, ValueError)
            else "connection_unavailable" if isinstance(error, psycopg.OperationalError)
            else "database_error"
        )
        delay = min(60, self.retry_seconds * 2 ** min(self._failures - 1, 4))
        self._retry_at = self.clock() + delay

    def _initialize(self, db):
        # Serialize schema initialization across API/collector processes.
        db.execute("SELECT pg_advisory_xact_lock(68424101)")
        db.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
        db.execute("CREATE SCHEMA IF NOT EXISTS bottleneck_busters")
        schema = re.sub(
            r"CREATE TABLE IF NOT EXISTS travel_time_obs \(.*?\n\);", "", SCHEMA, flags=re.DOTALL,
        )
        schema = schema.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGINT PRIMARY KEY")
        schema = schema.replace(" REAL", " DOUBLE PRECISION")
        schema = schema.replace(
            "CREATE TABLE IF NOT EXISTS sim_trials (",
            "CREATE TABLE IF NOT EXISTS simulation_trial_rows (replica_rowid BIGINT PRIMARY KEY,",
        ).replace("ON sim_trials(", "ON simulation_trial_rows(")
        schema = (schema + TRAVEL_SCHEMA + REPLICA_SCHEMA).replace(' TEXT', ' TEXT COLLATE "C"')
        for statement in schema.split(";"):
            if statement.strip():
                db.execute(statement)
        db.execute(
            "SELECT create_hypertable('travel_time_samples', 'observed_at',"
            " chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE)"
        )

    def _statement(self, table, operation, row):
        if table not in self.journal.columns:
            raise ValueError("Unrecognized journal table")
        columns = self.journal.columns[table].copy()
        keys = self.journal.keys[table].copy()
        values = dict(row)
        for column in self.journal.real_columns[table]:
            if values[column] is not None:
                values[column] = float(values[column])
        physical = table
        if table == "sim_trials":
            physical = "simulation_trial_rows"
            columns.append("replica_rowid")
        if table == "travel_time_obs":
            physical = "travel_time_samples"
            local = datetime.fromisoformat(values["city_updated_local"])
            if local.tzinfo is None:
                local = local.replace(tzinfo=ZoneInfo("America/Edmonton"), fold=0)
            values["observed_at"] = local.astimezone(UTC)
            columns.append("observed_at")
            keys.append("observed_at")
        if operation == "delete":
            where = sql.SQL(" AND ").join(
                sql.SQL("{}=%s").format(sql.Identifier(k)) for k in keys
            )
            return sql.SQL("DELETE FROM {} WHERE {}").format(sql.Identifier(physical), where), (
                tuple(values[k] for k in keys)
            )
        if operation != "upsert":
            raise ValueError("Unrecognized journal operation")
        update = sql.SQL(", ").join(
            sql.SQL("{}=excluded.{}").format(sql.Identifier(c), sql.Identifier(c))
            for c in columns if c not in keys
        )
        statement = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO UPDATE SET {}")
        statement = statement.format(
            sql.Identifier(physical), sql.SQL(", ").join(map(sql.Identifier, columns)),
            sql.SQL(", ").join(sql.Placeholder() for _ in columns),
            sql.SQL(", ").join(map(sql.Identifier, keys)), update,
        )
        return statement, tuple(values[c] for c in columns)

    def sync(self, force=False):
        if not force and self.clock() < self._retry_at:
            return False
        with self._lock:
            try:
                with self.connection() as db:
                    if not self._schema_ready:
                        self._initialize(db)
                    owned = db.execute("SELECT source_id FROM replica_state WHERE singleton=1"
                                       ).fetchone()
                    if owned is None:
                        # Never silently adopt an existing unowned dataset.
                        for table in self.journal.columns:
                            if db.execute(sql.SQL("SELECT EXISTS(SELECT 1 FROM {} LIMIT 1)")
                                          .format(sql.Identifier(table))).fetchone()[0]:
                                raise SourceMismatch()
                    db.execute(
                        "INSERT INTO replica_state(singleton, source_id) VALUES (1, %s)"
                        " ON CONFLICT(singleton) DO NOTHING", (self.journal.source_id,),
                    )
                    state = db.execute(
                        "SELECT source_id, applied_seq FROM replica_state WHERE singleton=1"
                        " FOR UPDATE"
                    ).fetchone()
                    local = self.journal.info()
                    if state[0] != self.journal.source_id or state[1] > local["latest_seq"]:
                        raise SourceMismatch()
                    events = self.journal.events_after(state[1], self.batch_size)
                    for (table, operation), group in groupby(events, key=lambda e: (e[1], e[2])):
                        commands = [self._statement(table, operation, e[3]) for e in group]
                        with db.cursor() as cursor:
                            cursor.executemany(commands[0][0], [c[1] for c in commands])
                    seq = events[-1][0] if events else state[1]
                    db.execute(
                        "UPDATE replica_state SET applied_seq=%s, last_sync_utc=now()"
                        " WHERE singleton=1", (seq,),
                    )
                # Remote transaction committed. Lost local acknowledgement is safe to retry.
                self._schema_ready = True
                self.journal.acknowledge(seq, utc_now())
                self.healthy, self.last_error = True, None
                self._failures, self._retry_at = 0, 0.0
                return self.journal.info()["pending_events"] == 0
            except (psycopg.Error, SourceMismatch, sqlite3.Error, OSError, ValueError) as error:
                self.failed(error)
                return False

    def status(self):
        state = self.journal.info()
        return {
            "configured_backend": "timescale",
            "active_backend": "timescale" if self.healthy and not state["pending_events"]
            else "sqlite",
            "primary_healthy": self.healthy,
            "pending_events": state["pending_events"],
            "last_sync_utc": state["last_sync_utc"],
            "last_error": self.last_error,
            "retry_in_s": round(max(0, self._retry_at - self.clock()), 1),
            "local_writes_durable": True,
        }
