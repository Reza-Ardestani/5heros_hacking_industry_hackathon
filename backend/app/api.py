import json
import os
import threading
from contextlib import asynccontextmanager
from urllib.request import Request, urlopen

import anyio
from fastapi import FastAPI, HTTPException
from fastapi import Request as HttpRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.application import disruptions, intersection_study
from app.application.assistant import SUGGESTIONS, Assistant, chat_mode
from app.application.jobs import BusyError, JobManager
from app.application.planner import PlanningService
from app.application.simulation_log import SimulationRecorder
from app.application.study_service import StudyService
from app.domain.models import Scenario
from app.infra import elevenlabs
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
    """Liveness check; also states that jobs are in memory with one active run."""
    return {"status": "ok", "mode": "local prototype", "jobs": "transient; one active run"}


@app.get("/api/scenario")
def scenario():
    """Default study inputs, synthetic network facts and the measured-arrival profile format."""
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
    """Calgary incident snapshot used as context for the guided study (offline, hashed)."""
    return load_incidents()


def _disruption_data(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/api/disruptions/summary")
def disruption_summary():
    """Headline counts, monthly trend, category mix, lane impact, top corridors and provenance."""
    return _disruption_data(disruptions.summary)


@app.get("/api/disruptions/intersections")
def disruption_intersections(
    q: str = "",
    quadrant: str = "",
    category: str = "",
    sort: str = "incidents",
    limit: int = 40,
    lat: float | None = None,
    lon: float | None = None,
    radius_m: float = 0,
):
    """Intersections ranked by reported incidents; filter by text, quadrant, category or area."""
    limit = max(1, min(limit, 200))
    return _disruption_data(
        disruptions.list_intersections, q, quadrant, category, sort, limit, lat, lon, radius_m
    )


@app.get("/api/disruptions/intersection")
def disruption_intersection(key: str):
    """Full profile of one intersection: signal, camera, volume, patterns, closures, recent
    incidents."""
    detail = _disruption_data(disruptions.intersection_detail, key)
    if detail is None:
        raise HTTPException(status_code=404, detail="Unknown intersection key")
    return detail


@app.get("/api/disruptions/options")
def disruption_options(quadrant: str = "", route: str = ""):
    """Valid areas, routes, directions, lanes, incident types and intersections for predictions."""
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
    model: str = "auto",
    lat: float | None = None,
    lon: float | None = None,
    radius_m: float = 0,
    area_label: str = "",
):
    """Forecast reported incidents for a selection: expected count, 80% range, per-period odds,
    model comparison and backtest."""
    if model not in disruptions.FORECAST_MODELS:
        raise HTTPException(
            status_code=422, detail=f"model must be one of {disruptions.FORECAST_MODELS}"
        )
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
        model,
        lat,
        lon,
        radius_m,
        area_label[:120],
    )


@app.get("/api/disruptions/priorities")
def disruption_priorities(
    level: str = "corridor",
    horizon_days: int = 28,
    quadrant: str = "",
    sort: str = "expected",
    limit: int = 15,
):
    """Where to study first: corridors or intersections ranked by forecast incidents, with ranges,
    recent change, ranking check and a simulatable study spot."""
    return _disruption_data(disruptions.priorities, level, horizon_days, quadrant, sort, limit)


@app.get("/api/ml-info")
def ml_info():
    """The three forecasting models, their settings and the model-selection rule."""
    return disruptions.ml_info()


@app.get("/api/ml/benchmark")
def ml_benchmark():
    """Flat vs Bayes vs LightGBM on standard selections: validation and test error, 80% range hit
    rate."""
    return _disruption_data(disruptions.ml_benchmark)


@app.get("/api/mcp-info")
def mcp_info(check: bool = False):
    """Describe the MCP server (mirrors its own /mcp-info) and whether it is reachable."""
    base = os.environ.get("BB_MCP_URL", "http://127.0.0.1:8000").rstrip("/")
    url = f"{base}/mcp-info" + ("?check=true" if check else "")
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=60) as r:
            info = json.loads(r.read())
        return {**info, "reachable": True, "probed_url": url}
    except (OSError, ValueError) as error:
        return {
            "reachable": False,
            "probed_url": url,
            "error": f"{type(error).__name__}: {error}",
            "how_to_start": "make mcp-http (serves http://127.0.0.1:8000/mcp)",
        }


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
    """Stored incidents (newest first) with parsed fields and live sightings."""
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
    """Stored City travel-time observations per segment."""
    return _disruption_data(disruptions.travel_time_history, corridor, segment, since, limit)


@app.get("/api/disruptions/status")
def disruption_status():
    """Database freshness: row counts, recent fetch runs and saved predictions."""
    return _disruption_data(disruptions.status)


@app.post("/api/disruptions/collect")
def disruption_collect(include_archive: bool = True):
    """Poll the City feeds now and append to the database (writes)."""
    return _disruption_data(disruptions.collect_now, include_archive)


@app.get("/api/disruptions/intersection/study")
def disruption_intersection_study(key: str):
    """Study inputs derived from one intersection's City data, with every assumption listed."""
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
    """Incidents and closures active right now (60 s cache), linked to historic hotspots."""
    return _disruption_data(disruptions.live, refresh)


assistant = Assistant()


class ChatTurn(BaseModel):
    role: str
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)


@app.post("/api/chat")
async def chat(body: ChatRequest):
    """Answer a question with the MCP tools; returns text plus UI actions."""
    return await assistant.reply(body.message, [t.model_dump() for t in body.history])


@app.get("/api/chat/info")
def chat_info():
    """Chat mode (builtin or Claude), available tools and suggested questions."""
    return {"mode": chat_mode(), "suggestions": SUGGESTIONS}


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


@app.get("/api/speech/info")
def speech_info():
    """Whether ElevenLabs text-to-speech is configured (ELEVENLABS_API_KEY) and its voice."""
    return elevenlabs.info()


@app.post("/api/speech", response_class=Response)
def speech(body: SpeechRequest):
    """Speak a chat reply with ElevenLabs; returns MP3 audio. 503 when no key is set."""
    try:
        audio = elevenlabs.synthesize(body.text)
    except elevenlabs.SpeechUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except elevenlabs.SpeechFailed as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return Response(audio, media_type="audio/mpeg", headers={"Cache-Control": "no-store"})


@app.post("/api/speech/transcribe")
async def speech_transcribe(request: HttpRequest):
    """Transcribe a spoken question (raw audio body, e.g. audio/webm) with ElevenLabs."""
    audio = await request.body()
    try:
        text = await anyio.to_thread.run_sync(
            elevenlabs.transcribe, audio, request.headers.get("content-type", "")
        )
    except elevenlabs.SpeechUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except elevenlabs.SpeechFailed as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"text": text}


@app.post("/api/jobs", status_code=202)
def submit(scenario: Scenario, origin: str = "manual", intersection_key: str = ""):
    """Start a simulation study (one active run at a time); poll /api/jobs/{job_id}."""
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
    """Recent simulation studies stored in the database."""
    return _disruption_data(disruptions.store().list_sims, max(1, min(limit, 200)))


@app.get("/api/simulations/{run_id}")
def simulation(run_id: str):
    """One stored study with its action log, options and every SUMO trial."""
    run = _disruption_data(disruptions.store().get_sim, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Unknown simulation run")
    return run


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    """Job status, agent events and, when complete, the result (incl. cost & budget stress test)."""
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job or expired local history")
    return job


@app.get("/api/jobs/{job_id}/report")
def report(job_id: str):
    """Download a completed study as a JSON evidence report."""
    job = get_job(job_id)
    if job["status"] != "completed":
        raise HTTPException(status_code=409, detail="Report requires a completed simulation")
    for alternative in job["result"]["alternatives"]:
        alternative["tuning_trial"].pop("playback", None)
    job["source_context"] = load_incidents()["source"]
    return JSONResponse(
        job, headers={"Content-Disposition": f'attachment; filename="bottleneck-{job_id}.json"'}
    )
