"""Shared Store facade: durable SQLite writes, optional Timescale reads and recovery."""

import os

from app.infra.sqlite_store import ROOT, SCHEMA, SQLiteStore, utc_now

__all__ = ["ROOT", "SCHEMA", "Store", "utc_now"]

WRITES = frozenset({
    "set_meta", "start_run", "finish_run", "upsert_incidents", "record_live_sightings",
    "upsert_closures", "add_travel_times", "put_reference", "save_prediction", "start_sim",
    "add_sim_action", "finish_sim", "fail_sim", "put_estimate",
})
READS = frozenset({
    "get_meta", "version", "runs", "latest_successful_runs", "incident_records",
    "query_incidents", "max_incident_start", "closure_records", "travel_times", "get_reference",
    "predictions", "list_sims", "get_sim", "latest_estimates", "get_estimate", "stats",
})


class Store:
    def __init__(self, path=None, *, backend=None, database_url=None, retry_seconds=5):
        mode = backend or os.environ.get("BB_DB_BACKEND", "sqlite")
        if mode not in {"sqlite", "timescale"}:
            raise ValueError("BB_DB_BACKEND must be sqlite or timescale")
        url = database_url or os.environ.get("BB_DATABASE_URL")
        if mode == "timescale" and (not url or not url.startswith(("postgresql://", "postgres://"))):
            raise ValueError("Timescale mode requires a PostgreSQL BB_DATABASE_URL")
        self.sqlite = SQLiteStore(path)
        self.path, self.mode = self.sqlite.path, mode
        self.mirror = self.primary = None
        if mode == "timescale":
            from app.infra.replica_journal import ReplicaJournal
            from app.infra.timescale_store import TimescaleMirror, TimescaleReadStore

            journal = ReplicaJournal(self.sqlite)
            self.mirror = TimescaleMirror(url, journal, retry_seconds=retry_seconds)
            self.primary = TimescaleReadStore(self.mirror, self.path)

    def connect(self):
        """Local transaction access; triggers also journal direct writes."""
        return self.sqlite.connect()

    def display_path(self):
        return self.sqlite.display_path()

    def sync(self, force=False):
        return self.mirror.sync(force=force) if self.mirror else True

    def storage_status(self):
        if self.mirror:
            return self.mirror.status()
        return {"configured_backend": "sqlite", "active_backend": "sqlite",
                "primary_healthy": None, "pending_events": 0, "last_sync_utc": None,
                "last_error": None, "retry_in_s": 0, "local_writes_durable": True}

    def __getattr__(self, name):
        if name not in READS | WRITES:
            raise AttributeError(name)

        def call(*args, **kwargs):
            if name in WRITES:
                result = getattr(self.sqlite, name)(*args, **kwargs)
                self.sync()
                return result
            target = self.primary if self.mirror and self.sync() else self.sqlite
            try:
                result = getattr(target, name)(*args, **kwargs)
            except Exception as error:
                if target is self.sqlite:
                    raise
                import psycopg

                if not isinstance(error, psycopg.Error):
                    raise
                self.mirror.failed(error)
                result = getattr(self.sqlite, name)(*args, **kwargs)
            if name == "stats":
                result["storage"] = self.storage_status()
                result["sqlite_bytes"] = self.path.stat().st_size
            return result

        return call
