from threading import Event

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.application.jobs import BusyError, JobManager
from app.domain.models import Scenario


def test_http_boundary_and_offline_sources():
    client = TestClient(app)
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/scenario").json()["network"]["kind"] == "synthetic"
    incidents = client.get("/api/incidents").json()
    assert incidents["raw_rows"] == incidents["source"]["rows"]
    assert 0 < incidents["context_events"] <= incidents["raw_rows"]
    assert incidents["records"] and incidents["source"]["sha256"]
    assert client.post("/api/jobs", json={"main_vph": -10}).status_code == 422
    assert client.get("/api/jobs/does-not-exist").status_code == 404


def test_busy_and_failed_job_release_slot_without_fake_success():
    started, release = Event(), Event()

    class FailingPlanner:
        def run(self, scenario, emit):
            started.set()
            release.wait(timeout=3)
            raise RuntimeError("Simulator unavailable")

    jobs = JobManager(FailingPlanner())
    job_id = jobs.submit(Scenario())
    assert started.wait(timeout=3)
    with pytest.raises(BusyError):
        jobs.submit(Scenario())
    release.set()
    jobs.pool.shutdown(wait=True)
    job = jobs.get(job_id)
    assert job["status"] == "failed" and job["result"] is None
    assert job["error"] == "Simulator unavailable"
    assert not jobs.active
