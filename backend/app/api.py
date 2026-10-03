from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.application.jobs import BusyError, JobManager
from app.application.planner import PlanningService
from app.domain.models import Scenario
from app.infra.incidents import load_incidents
from app.infra.simulation import SumoSimulator

app = FastAPI(title="Bottleneck Busters", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
jobs = JobManager(PlanningService(SumoSimulator()))


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "local prototype", "jobs": "transient; one active run"}


@app.get("/api/scenario")
def scenario():
    return {
        "defaults": Scenario().model_dump(),
        "network": {
            "kind": "synthetic",
            "junctions": 3,
            "arterial_length_m": 1600,
            "cycle_s": 90,
            "clearance_per_cycle_s": 10,
        },
        "profile_format": {
            "demand_kind": "measured",
            "demand_source": "Study URL/date/location",
            "duration_s": 900,
            "flow_profile": [{"begin_s": 0, "end_s": 900, "main_vph": 900, "cross_vph": 150}],
        },
    }


@app.get("/api/incidents")
def incidents():
    return load_incidents()


@app.post("/api/jobs", status_code=202)
def submit(scenario: Scenario):
    try:
        return {"id": jobs.submit(scenario), "status": "running"}
    except BusyError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job or expired local history")
    return job


@app.get("/api/jobs/{job_id}/report")
def report(job_id: str):
    job = get_job(job_id)
    if job["status"] != "completed":
        raise HTTPException(status_code=409, detail="Report requires a completed simulation")
    for alternative in job["result"]["alternatives"]:
        alternative["tuning_trial"].pop("playback", None)
    job["source_context"] = load_incidents()["source"]
    return JSONResponse(
        job, headers={"Content-Disposition": f'attachment; filename="bottleneck-{job_id}.json"'}
    )
