"""Opt-in disposable real Timescale container tests: BB_TEST_TIMESCALE=1 pytest ..."""

import asyncio
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from mcp.shared.memory import create_connected_server_and_client_session

from app.api import app
from app.application import disruptions
from app.application.disruption_collector import seed_from_exports
from app.application.jobs import JobManager
from app.application.planner import PlanningService
from app.application.simulation_log import SimulationRecorder
from app.domain.models import Scenario
from app.infra.disruption_store import Store
from app.infra.simulation import SumoSimulator
from app.mcp_server import build_server

pytestmark = pytest.mark.skipif(
    os.environ.get("BB_TEST_TIMESCALE") != "1", reason="real Timescale container test is opt-in",
)
IMAGE = "timescale/timescaledb:2.23.1-pg17"


def docker(*args):
    result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=90,
                            check=False)
    if result.returncode:
        raise RuntimeError("Disposable Timescale Docker command failed")
    return result.stdout.strip()


class Harness:
    def __init__(self):
        self.name = "bb-timescale-test-" + uuid4().hex[:10]
        self.volume = self.name + "-data"
        self.password = secrets.token_urlsafe(24)
        self.port = None

    def start(self):
        docker("run", "-d", "--name", self.name, "-e", "POSTGRES_PASSWORD=" + self.password,
               "-e", "POSTGRES_DB=bb_test", "-p", f"127.0.0.1:{self.port or ''}:5432",
               "-v", self.volume + ":/var/lib/postgresql/data", IMAGE)
        self.port = docker("port", self.name, "5432/tcp").rsplit(":", 1)[1]
        self.wait()

    @property
    def url(self):
        return f"postgresql://postgres:{self.password}@127.0.0.1:{self.port}/bb_test"

    def wait(self):
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            try:
                with psycopg.connect(self.url, connect_timeout=2) as db:
                    db.execute("SELECT 1")
                return
            except psycopg.OperationalError:
                time.sleep(0.25)
        raise RuntimeError("Disposable Timescale did not become ready")

    def replace_container(self):
        docker("rm", "-f", self.name)
        self.start()


@pytest.fixture(scope="module")
def server():
    harness = Harness()
    try:
        harness.start()
        yield harness
    finally:
        subprocess.run(["docker", "rm", "-f", harness.name], capture_output=True, timeout=30,
                       check=False)
        subprocess.run(["docker", "volume", "rm", harness.volume], capture_output=True, timeout=30,
                       check=False)


@pytest.fixture
def destination(server, seeded_store):
    # This schema exists only in the disposable test database.
    with psycopg.connect(server.url) as db:
        db.execute("DROP SCHEMA IF EXISTS bottleneck_busters CASCADE")
    yield server
    disruptions.use_store(seeded_store)


def drain(store):
    for _ in range(30):
        if store.sync(force=True):
            assert store.storage_status()["active_backend"] == "timescale"
            return
        assert store.storage_status()["last_error"] is None, store.storage_status()
    raise AssertionError("Mirror did not catch up")


def new_store(path, server):
    return Store(path, backend="timescale", database_url=server.url, retry_seconds=0)


def test_bootstrap_real_hypertable_api_and_simulation_parity(destination, tmp_path, monkeypatch):
    def no_city(*args, **kwargs):
        raise AssertionError("Migration must not call City APIs")

    monkeypatch.setattr("app.infra.city_open_data.fetch", no_city)
    local = Store(tmp_path / "legacy.sqlite", backend="sqlite")
    assert seed_from_exports(local, disruptions.ANALYSIS)
    store = new_store(local.path, destination)
    drain(store)
    assert store.incident_records() == local.incident_records()
    assert store.query_incidents({"quadrant": "SW"}, limit=20) == local.query_incidents(
        {"quadrant": "SW"}, limit=20,
    )
    assert store.closure_records() == local.closure_records()
    assert store.travel_times() == local.travel_times()
    assert store.get_reference("cameras") == local.get_reference("cameras")
    assert store.runs() == local.runs()
    assert store.version() == local.version()
    assert store.latest_successful_runs() == local.latest_successful_runs()
    assert store.max_incident_start("archive") == local.max_incident_start("archive")

    result = {"forecast_start": "2026-10-05", "horizon_days": 7, "expected_total": 4.2,
              "interval_80": [2, 7]}
    prediction_id = store.save_prediction("test", {"quadrant": "SW"}, result)
    assert store.predictions()[0]["id"] == prediction_id
    assert store.predictions() == local.predictions()
    store.put_estimate("test", "sha", {"modeled": True})
    assert store.get_estimate("test", "sha") == local.get_estimate("test", "sha")
    assert store.latest_estimates() == local.latest_estimates()

    recorder = SimulationRecorder(lambda: store, runs_dir=tmp_path / "runs")
    jobs = JobManager(PlanningService(SumoSimulator()), recorder)
    run_id = jobs.submit(Scenario(duration_s=300), {"origin": "timescale-test"})
    jobs.pool.shutdown(wait=True)
    assert jobs.get(run_id)["status"] == "completed"
    assert store.get_sim(run_id) == local.get_sim(run_id)
    assert len(store.get_sim(run_id)["trials"]) == 20
    store.start_sim("failed", {"test": True})
    store.fail_sim("failed", "test failure")
    assert store.list_sims() == local.list_sims()
    with store.mirror.connection() as db:
        assert db.execute(
            "SELECT hypertable_name FROM timescaledb_information.hypertables"
            " WHERE hypertable_schema='bottleneck_busters'"
        ).fetchone()[0] == "travel_time_samples"
        assert db.execute("SELECT pg_typeof(observed_at)::text FROM travel_time_samples LIMIT 1"
                          ).fetchone()[0] == "timestamp with time zone"
    disruptions.use_store(store)
    response = TestClient(app).get("/api/disruptions/status")
    assert response.status_code == 200
    assert response.json()["storage"]["active_backend"] == "timescale"
    assert destination.password not in json.dumps(response.json())

    async def agent_reads():
        async with create_connected_server_and_client_session(build_server()._mcp_server) as client:
            status = await client.call_tool("get_data_status", {})
            assert not status.isError
            assert json.loads(status.content[0].text)["storage"]["active_backend"] == "timescale"
            result = await client.call_tool("get_simulation_run", {"run_id": run_id})
            assert not result.isError
            assert json.loads(result.content[0].text) == local.get_sim(run_id)

    asyncio.run(agent_reads())
    cli = subprocess.run(
        [sys.executable, "../scripts/sync_storage.py"],
        env={**os.environ, "BB_DB_BACKEND": "timescale", "BB_DATABASE_URL": destination.url,
             "BB_DB_PATH": str(store.path)}, capture_output=True, text=True, timeout=30,
        check=False,
    )
    assert cli.returncode == 0, "Offline sync CLI failed"
    assert json.loads(cli.stdout)["active_backend"] == "timescale"
    assert destination.password not in cli.stdout


def test_outage_restart_lost_ack_empty_destination_and_persistent_volume(destination, tmp_path,
                                                                      monkeypatch):
    path = tmp_path / "durable.sqlite"
    store = new_store(path, destination)
    rec = {"uid": "event", "start_utc": "2026-10-03T12:00:00",
           "start_local": "2026-10-03T06:00:00", "last_update_utc": "2026-10-03T12:01:00"}
    store.upsert_incidents([rec], "live")
    store.record_live_sightings(["event"])
    drain(store)
    initial = store.incident_records()
    destination.replace_container()
    assert store.incident_records() == initial
    assert store.storage_status()["active_backend"] == "timescale"

    docker("stop", "-t", "1", destination.name)
    store.record_live_sightings(["event"])
    store.set_meta("offline", {"preserved": True})
    assert store.incident_records()[0]["live_sightings"] == 2
    assert store.stats()["storage"]["active_backend"] == "sqlite"
    restarted = new_store(path, destination)
    assert restarted.get_meta("offline") == {"preserved": True}
    assert restarted.incident_records()[0]["live_sightings"] == 2
    assert restarted.storage_status()["pending_events"] > 0
    docker("start", destination.name)
    destination.wait()
    drain(restarted)

    acknowledge = restarted.mirror.journal.acknowledge

    def lost_ack(*args):
        raise sqlite3.OperationalError("local ack interrupted")

    monkeypatch.setattr(restarted.mirror.journal, "acknowledge", lost_ack)
    restarted.record_live_sightings(["event"])
    assert restarted.storage_status()["last_error"] == "local_ack_failed"
    assert restarted.storage_status()["pending_events"] > 0
    monkeypatch.setattr(restarted.mirror.journal, "acknowledge", acknowledge)
    drain(restarted)
    assert restarted.incident_records()[0]["live_sightings"] == 3
    with restarted.mirror.connection() as db:
        assert db.execute("SELECT live_sightings FROM incidents WHERE uid='event'").fetchone()[0] == 3

    # An empty destination rebuilds from retained events, with no City API call.
    with psycopg.connect(destination.url) as db:
        db.execute("DROP SCHEMA bottleneck_busters CASCADE")
    # The already-running adapter detects the missing schema, then reinitializes.
    assert restarted.sync(force=True) is False
    rebuilt = restarted
    drain(rebuilt)
    assert rebuilt.get_meta("offline") == {"preserved": True}
    assert rebuilt.incident_records()[0]["live_sightings"] == 3
    assert rebuilt.incident_records() == rebuilt.sqlite.incident_records()


def test_shared_file_concurrency_and_foreign_source_rejection(destination, tmp_path):
    path = tmp_path / "shared.sqlite"
    first = new_store(path, destination)
    second = new_store(path, destination)
    assert first.mirror.journal.source_id == second.mirror.journal.source_id
    rec = {"uid": "shared", "start_utc": "2026-10-03T12:00:00",
           "start_local": "2026-10-03T06:00:00"}
    first.upsert_incidents([rec], "live")

    def write(i):
        (first if i % 2 else second).record_live_sightings(["shared"])

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write, range(12)))
    worker = """
import json, sys
from app.infra.disruption_store import Store
settings = json.load(sys.stdin)
store = Store(settings['path'], backend='timescale', database_url=settings['url'], retry_seconds=0)
for _ in range(4):
    store.record_live_sightings(['shared'])
"""
    # Independent Python processes share the durable SQLite history; the URL is
    # delivered on stdin, never as a command argument or test output.
    workers = [subprocess.Popen([sys.executable, "-c", worker], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
               for _ in range(3)]
    for process in workers:
        process.stdin.write(json.dumps({"path": str(path), "url": destination.url}))
        process.stdin.close()
        process.stdin = None
    for process in workers:
        process.communicate(timeout=45)
        assert process.returncode == 0, "Shared-file writer process failed"
    drain(first)
    assert first.incident_records()[0]["live_sightings"] == 24
    with first.mirror.connection() as db:
        assert db.execute("SELECT live_sightings FROM incidents WHERE uid='shared'").fetchone()[0] == 24
    alien = new_store(tmp_path / "independent.sqlite", destination)
    alien.set_meta("foreign", True)
    assert alien.get_meta("foreign") is True  # isolated local fallback
    assert alien.storage_status()["last_error"] == "source_mismatch"
    assert first.get_meta("foreign") is None


def test_failed_batch_rolls_back_checkpoint_and_rows(destination, tmp_path):
    store = new_store(tmp_path / "rollback.sqlite", destination)
    drain(store)
    with store.mirror.connection() as db:
        initial = db.execute("SELECT applied_seq FROM replica_state").fetchone()[0]
        db.execute("ALTER TABLE meta ADD CONSTRAINT test_blocked CHECK (key <> 'blocked')")
    with store.connect() as db:
        db.execute("INSERT INTO meta VALUES ('valid', 'true')")
        db.execute("INSERT INTO meta VALUES ('blocked', 'true')")
    assert store.sync(force=True) is False
    assert store.storage_status()["active_backend"] == "sqlite"
    assert store.sqlite.get_meta("valid") is True
    with store.mirror.connection() as db:
        assert db.execute("SELECT applied_seq FROM replica_state").fetchone()[0] == initial
        assert db.execute("SELECT COUNT(*) FROM meta WHERE key='valid'").fetchone()[0] == 0
        db.execute("ALTER TABLE meta DROP CONSTRAINT test_blocked")
    drain(store)
    assert store.get_meta("valid") is True
    assert store.get_meta("blocked") is True
