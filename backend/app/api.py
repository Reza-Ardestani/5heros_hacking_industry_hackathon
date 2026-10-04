import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.application import disruptions, intersection_study
from app.application.jobs import BusyError, JobManager
from app.application.planner import PlanningService
from app.application.simulation_log import SimulationRecorder
from app.application.study_service import StudyService
from app.domain.models import Scenario
from app.infra.incidents import load_incidents
from app.infra.simulation import SumoSimulator


def _background_collector(every_s: int, stop: threading.Event):
    """Optional in-process poller (BB_COLLECT_EVERY_S); the CLI collector is the default."""
    while not stop.wait(every_s):
        try:
            disruptions.collect_now(include_archive=True)
        except Exception as error:  # noqa: BLE001 — failures are recorded in fetch_runs
            print(f"[collector] {type(error).__name__}: {error}")


@asynccontextmanager
async def lifespan(_app):
    stop = threading.Event()
    every = int(os.environ.get("BB_COLLECT_EVERY_S", "0") or 0)
    if every > 0:
        threading.Thread(
            target=_background_collector, args=(max(60, every), stop), daemon=True
        ).start()
    yield
    stop.set()


app = FastAPI(title="Bottleneck Busters", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],  # POST /api/disruptions/collect triggers a poll
    allow_headers=["Content-Type"],
)
simulator = SumoSimulator()
jobs = JobManager(StudyService(PlanningService(simulator)), SimulationRecorder(disruptions.store))


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


def _disruption_data(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/api/disruptions/summary")
def disruption_summary():
    return _disruption_data(disruptions.summary)


@app.get("/api/disruptions/intersections")
def disruption_intersections(
    q: str = "", quadrant: str = "", category: str = "", sort: str = "incidents", limit: int = 40
):
    limit = max(1, min(limit, 200))
    return _disruption_data(disruptions.list_intersections, q, quadrant, category, sort, limit)


@app.get("/api/disruptions/intersection")
def disruption_intersection(key: str):
    detail = _disruption_data(disruptions.intersection_detail, key)
    if detail is None:
        raise HTTPException(status_code=404, detail="Unknown intersection key")
    return detail


@app.get("/api/disruptions/options")
def disruption_options(quadrant: str = "", route: str = ""):
    return _disruption_data(disruptions.options, quadrant, route)


@app.get("/api/disruptions/predict")
def disruption_predict(
    quadrant: str = "",
    route: str = "",
    direction: str = "",
    lane: str = "",
    category: str = "",
    intersection: str = "",
    horizon_days: int = 7,
    save: bool = False,
):
    return _disruption_data(
        disruptions.predict,
        quadrant,
        route,
        direction,
        lane,
        category,
        intersection,
        horizon_days,
        save,
        "api",
    )


@app.get("/api/disruptions/history")
def disruption_history(
    route: str = "",
    intersection: str = "",
    quadrant: str = "",
    category: str = "",
    lane: str = "",
    direction: str = "",
    since: str = "",
    until: str = "",
    limit: int = 100,
):
    return _disruption_data(
        disruptions.incident_history,
        route,
        intersection,
        quadrant,
        category,
        lane,
        direction,
        since,
        until,
        limit,
    )


@app.get("/api/disruptions/travel-times")
def disruption_travel_times(
    corridor: str = "", segment: str = "", since: str = "", limit: int = 500
):
    return _disruption_data(disruptions.travel_time_history, corridor, segment, since, limit)


@app.get("/api/disruptions/status")
def disruption_status():
    return _disruption_data(disruptions.status)


@app.post("/api/disruptions/collect")
def disruption_collect(include_archive: bool = True):
    return _disruption_data(disruptions.collect_now, include_archive)


@app.get("/api/disruptions/intersection/study")
def disruption_intersection_study(key: str):
    study = _disruption_data(intersection_study.build_study, key)
    if study is None:
        raise HTTPException(status_code=404, detail="Unknown intersection key")
    return study


@app.get("/api/disruptions/intersection/estimate")
def disruption_intersection_estimate(key: str, refresh: bool = False):
    """Modeled seconds of delay per vehicle from one typical incident (runs SUMO, cached)."""
    estimate = _disruption_data(intersection_study.estimate_incident_delay, key, simulator, refresh)
    if estimate is None:
        raise HTTPException(status_code=404, detail="Unknown intersection key")
    return estimate


@app.get("/api/disruptions/live")
def disruption_live(refresh: bool = False):
    return _disruption_data(disruptions.live, refresh)


@app.post("/api/jobs", status_code=202)
def submit(scenario: Scenario, origin: str = "manual", intersection_key: str = ""):
    meta = {"origin": origin[:40]}
    if intersection_key:
        context = _disruption_data(intersection_study.context_for, intersection_key)
        if context is None:
            raise HTTPException(status_code=404, detail="Unknown intersection key")
        meta.update(intersection_key=intersection_key, context=context)
    try:
        return {"id": jobs.submit(scenario, meta), "status": "running"}
    except BusyError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/api/simulations")
def simulations(limit: int = 20):
    return _disruption_data(disruptions.store().list_sims, max(1, min(limit, 200)))


@app.get("/api/simulations/{run_id}")
def simulation(run_id: str):
    run = _disruption_data(disruptions.store().get_sim, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Unknown simulation run")
    return run


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
