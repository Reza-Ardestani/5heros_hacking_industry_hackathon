"""Atomic SQLite row journal. Retained history rebuilds an empty Timescale mirror."""

import json
from uuid import uuid4

TABLES = (
    "meta", "fetch_runs", "incidents", "closures", "travel_time_obs", "reference_layers",
    "predictions", "sim_runs", "sim_actions", "sim_alternatives", "sim_trials",
    "intersection_estimates",
)


class ReplicaJournal:
    def __init__(self, store):
        self.store = store
        self.columns, self.keys, self.real_columns = {}, {}, {}
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "CREATE TABLE IF NOT EXISTS replica_state (singleton INTEGER PRIMARY KEY"
                " CHECK(singleton=1), source_id TEXT NOT NULL, acknowledged_seq INTEGER NOT NULL"
                " DEFAULT 0, last_sync_utc TEXT)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS replica_events (seq INTEGER PRIMARY KEY AUTOINCREMENT,"
                " table_name TEXT NOT NULL, operation TEXT NOT NULL, row_json TEXT NOT NULL)"
            )
            row = db.execute("SELECT source_id FROM replica_state WHERE singleton=1").fetchone()
            fresh = row is None
            self.source_id = row[0] if row else str(uuid4())
            if fresh:
                db.execute("INSERT INTO replica_state(singleton, source_id) VALUES (1, ?)",
                           (self.source_id,))
            for table in TABLES:
                fields = db.execute(f'PRAGMA table_info("{table}")').fetchall()
                self.columns[table] = [r[1] for r in fields]
                self.real_columns[table] = [r[1] for r in fields if r[2].upper() == "REAL"]
                self.keys[table] = [r[1] for r in sorted(fields, key=lambda r: r[5]) if r[5]]
                if table == "sim_trials":
                    self.keys[table] = ["replica_rowid"]
                for event, prefix, operation in (
                    ("INSERT", "NEW", "upsert"), ("UPDATE", "NEW", "upsert"),
                    ("DELETE", "OLD", "delete"),
                ):
                    payload = self._json_expression(table, prefix + ".")
                    db.execute(
                        f'CREATE TRIGGER IF NOT EXISTS "replica_{table}_{event.lower()}" '
                        f'AFTER {event} ON "{table}" BEGIN '
                        "INSERT INTO replica_events(table_name, operation, row_json) "
                        f"VALUES ('{table}', '{operation}', {payload}); END"
                    )
                if fresh:
                    payload = self._json_expression(table)
                    db.execute(
                        "INSERT INTO replica_events(table_name, operation, row_json) "
                        f"SELECT '{table}', 'upsert', {payload} FROM \"{table}\""
                    )

    def _json_expression(self, table, prefix=""):
        pairs = []
        for column in self.columns[table]:
            value = f'{prefix}"{column}"'
            if column in self.real_columns[table]:
                # JSON1's default number formatting loses double precision. Keep
                # a round-trip decimal string; the mirror restores the float.
                value = f"CASE WHEN {value} IS NULL THEN NULL ELSE printf('%!.26g', {value}) END"
            pairs.append(f"'{column}', {value}")
        if table == "sim_trials":
            pairs.append(f"'replica_rowid', {prefix}rowid")
        return "json_object(" + ", ".join(pairs) + ")"

    def info(self):
        with self.store.connect() as db:
            state = dict(db.execute("SELECT * FROM replica_state WHERE singleton=1").fetchone())
            state["latest_seq"] = db.execute(
                "SELECT COALESCE(MAX(seq), 0) FROM replica_events"
            ).fetchone()[0]
            state["pending_events"] = db.execute(
                "SELECT COUNT(*) FROM replica_events WHERE seq > ?",
                (state["acknowledged_seq"],),
            ).fetchone()[0]
            return state

    def events_after(self, seq, limit):
        with self.store.connect() as db:
            return [
                (r["seq"], r["table_name"], r["operation"], json.loads(r["row_json"]))
                for r in db.execute(
                    "SELECT * FROM replica_events WHERE seq > ? ORDER BY seq LIMIT ?", (seq, limit)
                )
            ]

    def acknowledge(self, seq, at):
        with self.store.connect() as db:
            db.execute(
                "UPDATE replica_state SET acknowledged_seq=?, last_sync_utc=? WHERE singleton=1",
                (seq, at),
            )
