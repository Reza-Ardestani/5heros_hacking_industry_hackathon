"""Durability and degraded-mode tests; real Timescale lifecycle lives in integration suite."""

import json
import sqlite3

import psycopg
import pytest

from app.infra.disruption_store import ROOT, Store
from app.infra.replica_journal import ReplicaJournal


def test_default_and_bad_configuration(tmp_path, monkeypatch):
    monkeypatch.delenv("BB_DB_BACKEND", raising=False)
    store = Store(tmp_path / "plain.sqlite")
    store.set_meta("example", {"value": 1})
    assert store.get_meta("example") == {"value": 1}
    assert store.stats()["storage"]["active_backend"] == "sqlite"
    with pytest.raises(ValueError, match="BB_DB_BACKEND"):
        Store(tmp_path / "invalid.sqlite", backend="unknown")
    with pytest.raises(ValueError, match="BB_DATABASE_URL"):
        Store(tmp_path / "invalid.sqlite", backend="timescale", database_url="sqlite://local")
    monkeypatch.setenv("BB_DB_PATH", "data/db/example.sqlite")
    # Relative configured paths resolve identically for API and root CLI processes.
    monkeypatch.setattr("app.infra.sqlite_store.ROOT", tmp_path)
    assert Store(backend="sqlite").path == tmp_path / "data/db/example.sqlite"
    assert ROOT.name == "5heros_hacking_industry_hackathon"


def test_journal_snapshot_atomic_rollback_and_stable_identity(tmp_path):
    store = Store(tmp_path / "db.sqlite", backend="sqlite")
    store.set_meta("existing", {"preserved": True})
    journal = ReplicaJournal(store.sqlite)
    events = journal.events_after(0, 100)
    assert any(e[1] == "meta" and e[3]["key"] == "existing" for e in events)
    seq = journal.info()["latest_seq"]
    with pytest.raises(RuntimeError, match="rollback"), store.connect() as db:
        db.execute("INSERT INTO meta VALUES ('discarded', 'true')")
        raise RuntimeError("rollback")
    assert store.get_meta("discarded") is None
    assert journal.info()["latest_seq"] == seq
    store.set_meta("existing", {"preserved": False})
    assert journal.info()["latest_seq"] == seq + 1
    again = ReplicaJournal(Store(tmp_path / "db.sqlite", backend="sqlite").sqlite)
    assert again.source_id == journal.source_id
    assert again.info()["latest_seq"] == seq + 2  # existing schema-version write also journaled


def test_outage_backoff_redaction_and_offline_restart(tmp_path, monkeypatch):
    calls, clock = [], [100.0]

    def unavailable(*args, **kwargs):
        calls.append(1)
        raise psycopg.OperationalError("password=do-not-expose-this-secret")

    monkeypatch.setattr(psycopg, "connect", unavailable)
    path = tmp_path / "db.sqlite"
    store = Store(path, backend="timescale", database_url="postgresql://localhost/unreachable")
    store.mirror.clock = lambda: clock[0]
    store.set_meta("offline", {"durable": True})
    assert store.get_meta("offline") == {"durable": True}
    assert len(calls) == 1  # reads and writes respect backoff
    state = store.stats()["storage"]
    assert state["active_backend"] == "sqlite" and state["pending_events"] > 0
    assert state["retry_in_s"] == 5 and state["last_error"] == "connection_unavailable"
    assert "do-not-expose" not in json.dumps(state)
    clock[0] += 5
    store.get_meta("offline")
    assert len(calls) == 2 and store.storage_status()["retry_in_s"] == 10
    restarted = Store(path, backend="timescale", database_url="postgresql://localhost/unreachable")
    assert restarted.get_meta("offline") == {"durable": True}
    assert restarted.mirror.journal.source_id == store.mirror.journal.source_id


def test_failed_local_write_is_not_acknowledged(tmp_path, monkeypatch):
    store = Store(tmp_path / "db.sqlite", backend="sqlite")

    def full_disk(*args, **kwargs):
        raise sqlite3.OperationalError("database or disk is full")

    monkeypatch.setattr(store.sqlite, "set_meta", full_disk)
    with pytest.raises(sqlite3.OperationalError, match="disk is full"):
        store.set_meta("lost", True)


def test_trigger_preserves_float_precision_and_nulls(tmp_path):
    store = Store(tmp_path / "db.sqlite", backend="sqlite")
    journal = ReplicaJournal(store.sqlite)
    value = 131.75495733558284
    with store.connect() as db:
        db.execute("INSERT INTO travel_time_obs VALUES (?, NULL, ?, ?, ?)",
                   ("precision", "2026-10-04T12:00:00", value, "2026-10-04T18:00:00"))
    row = journal.events_after(0, 100)[-1][3]
    assert float(row["travel_time_min"]) == value
    assert row["corridor"] is None


def test_read_failure_retries_whole_read_locally(tmp_path, monkeypatch):
    store = Store(tmp_path / "db.sqlite", backend="timescale",
                  database_url="postgresql://localhost/not-used")
    store.sqlite.set_meta("offline", True)
    monkeypatch.setattr(store.mirror, "sync", lambda **kwargs: True)

    def failed_read(*args, **kwargs):
        raise psycopg.OperationalError("password=do-not-expose-this-secret")

    monkeypatch.setattr(store.primary, "get_meta", failed_read)
    assert store.get_meta("offline") is True
    assert store.storage_status()["active_backend"] == "sqlite"
    assert "do-not-expose" not in json.dumps(store.storage_status())
