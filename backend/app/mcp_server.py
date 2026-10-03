"""MCP server exposing the Calgary disruption database and forecasts as agent tools.

Same service layer as the HTTP API (app/application/disruptions.py), so an agent
sees exactly what the UI shows. Two transports:

  stdio (local agents, Claude Code/Desktop):
      uv run --group mcp python -m app.mcp_server
  streamable HTTP, stateless (Amazon Bedrock AgentCore Runtime contract:
  0.0.0.0:8000/mcp):
      uv run --group mcp python -m app.mcp_server --transport streamable-http --host 0.0.0.0

Writes: predict_disruptions(save=True) stores a prediction; collect_latest_data polls
the City and appends to the database (disable with BB_MCP_ALLOW_COLLECT=0).
"""

import argparse
import os
import time
from typing import Annotated, Literal

import anyio
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.application import disruptions, intersection_study

INSTRUCTIONS = """\
Calgary traffic disruption data (City of Calgary Open Data, Open Government Licence –
City of Calgary): six months+ of camera-reported incidents, road/lane closures, travel
times, cameras, signals and 2024 volumes, stored in a database that a collector keeps
up to date. Typical flow: get_prediction_options -> predict_disruptions; or
search_intersections -> get_intersection_details. Counts are reported disruptions,
not traffic flow, delay or crash risk; always pass the caveat on to users and quote the
backtest verdict when presenting a prediction."""

READ = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
READ_LIVE = ToolAnnotations(readOnlyHint=False, idempotentHint=True, openWorldHint=True)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False)

Quadrant = Annotated[str, Field(description="City quadrant: NE, NW, SE, SW, or empty for all")]
Route = Annotated[
    str,
    Field(description="Route/corridor key from get_prediction_options, e.g. 'Deerfoot Trail' "
          "or '16 Avenue NE'; empty for all"),
]  # fmt: skip
Latitude = Annotated[float | None, Field(description="Area centre latitude (WGS84)")]
Longitude = Annotated[float | None, Field(description="Area centre longitude (WGS84)")]
RadiusM = Annotated[float, Field(ge=0, le=10000, description="Area radius in metres; 0 = none")]
Intersection = Annotated[
    str, Field(description="Intersection key, e.g. 'Deerfoot Trail & Glenmore Trail SE'")
]


async def _run(fn, *args):
    # Tools touch SQLite and the network; keep the event loop free.
    return await anyio.to_thread.run_sync(lambda: fn(*args))


def build_server(host="127.0.0.1", port=8000, stateless=False):
    mcp = FastMCP(
        "calgary-traffic-disruptions",
        instructions=INSTRUCTIONS,
        host=host,
        port=port,
        streamable_http_path="/mcp",
        stateless_http=stateless,
        json_response=stateless,
    )

    @mcp.tool(annotations=READ)
    async def get_disruption_summary() -> dict:
        """Headline counts, monthly trend, category mix, lane impact, top corridors and
        data provenance (sources, hashes, database path) for the rolling window."""
        return await _run(disruptions.summary)

    @mcp.tool(annotations=READ)
    async def get_prediction_options(quadrant: Quadrant = "", route: Route = "") -> dict:
        """Valid values for areas, routes, directions, lanes, incident types and (when a
        route is given) intersections, each with its historical incident count."""
        return await _run(disruptions.options, quadrant, route)

    @mcp.tool(annotations=READ)
    async def search_intersections(
        query: Annotated[
            str, Field(description="Case-insensitive text in the intersection name")
        ] = "",
        quadrant: Quadrant = "",
        category: Annotated[str, Field(description="Incident group, e.g. 'Collision'")] = "",
        sort: Literal["incidents", "lane_blocking", "collisions", "recent"] = "incidents",
        limit: Annotated[int, Field(ge=1, le=100)] = 20,
        lat: Latitude = None,
        lon: Longitude = None,
        radius_m: RadiusM = 0,
    ) -> dict:
        """Rank intersections by reported incidents in the window, optionally only those
        within radius_m of (lat, lon)."""
        return await _run(
            disruptions.list_intersections, query, quadrant, category, sort, limit, lat, lon,
            radius_m,
        )  # fmt: skip

    @mcp.tool(annotations=READ)
    async def get_intersection_details(key: Intersection) -> dict:
        """Full profile of one intersection: signal, live camera image URL, 2024 volume,
        incident types, lane impact, direction, hour/weekday/month pattern, nearby
        closures and the 25 most recent incidents."""
        detail = await _run(disruptions.intersection_detail, key)
        if detail is None:
            raise ValueError(f"Unknown intersection key {key!r}; use search_intersections")
        return detail

    @mcp.tool(annotations=WRITE)
    async def predict_disruptions(
        quadrant: Quadrant = "",
        route: Route = "",
        direction: Annotated[str, Field(description="NB, SB, EB, WB or empty")] = "",
        lane: Annotated[str, Field(description="Lane position, e.g. 'Right lane'")] = "",
        category: Annotated[str, Field(description="Incident group, e.g. 'Collision'")] = "",
        intersection: Intersection = "",
        horizon_days: Annotated[int, Field(ge=1, le=28)] = 7,
        save: Annotated[bool, Field(description="Store the forecast for later scoring")] = True,
        model: Literal["auto", "flat", "bayes", "lightgbm"] = "auto",
        lat: Latitude = None,
        lon: Longitude = None,
        radius_m: RadiusM = 0,
    ) -> dict:
        """Forecast reported incidents for a selection over the next 1-28 days: expected
        count, 80% range, per-day x period probabilities, likely types/locations, and a
        28-day backtest against a flat-average baseline (report its verdict). model="auto"
        uses whichever of flat / empirical-Bayes / LightGBM won on validation days."""
        return await _run(
            disruptions.predict, quadrant, route, direction, lane, category, intersection,
            horizon_days, save, "mcp", model, lat, lon, radius_m,
        )  # fmt: skip

    @mcp.tool(annotations=READ)
    async def query_incident_history(
        route: Route = "",
        intersection: Intersection = "",
        quadrant: Quadrant = "",
        category: Annotated[str, Field(description="Incident group, e.g. 'Signal fault'")] = "",
        lane: str = "",
        direction: str = "",
        since: Annotated[str, Field(description="Local start, 'YYYY-MM-DD[ HH:MM]'")] = "",
        until: Annotated[str, Field(description="Local end (exclusive)")] = "",
        limit: Annotated[int, Field(ge=1, le=500)] = 100,
    ) -> dict:
        """Individual stored incidents (newest first) with parsed fields and, for incidents
        seen in the live feed, first/last sighting times."""
        return await _run(
            disruptions.incident_history, route, intersection, quadrant, category, lane,
            direction, since, until, limit,
        )  # fmt: skip

    @mcp.tool(annotations=READ)
    async def get_travel_time_history(
        corridor: Annotated[str, Field(description="e.g. 'Deerfoot Trail'")] = "",
        segment: str = "",
        since: Annotated[str, Field(description="Local time 'YYYY-MM-DDTHH:MM'")] = "",
        limit: Annotated[int, Field(ge=1, le=5000)] = 500,
    ) -> dict:
        """Stored City travel-time observations (one per segment per City update)."""
        return await _run(disruptions.travel_time_history, corridor, segment, since, limit)

    @mcp.tool(annotations=READ_LIVE)
    async def get_live_disruptions(refresh: bool = False) -> dict:
        """Incidents and closures active right now (City API, 60 s cache), each linked to
        the nearest historic hotspot. Results are also stored in the database."""
        return await _run(disruptions.live, refresh)

    @mcp.tool(annotations=READ)
    async def get_data_status() -> dict:
        """Database freshness: row counts, live sightings, removed closures, travel-time
        observations, recent fetch runs (with failures) and saved predictions."""
        return await _run(disruptions.status)

    @mcp.tool(annotations=READ)
    async def build_intersection_study(key: Intersection) -> dict:
        """Corridor-study inputs derived from one intersection's City data: demand from 2024
        volumes, lanes, signal status, typical incident (lanes, direction, duration) and its
        frequency weight, with every assumption listed. Run it in the app's step 2."""
        study = await _run(intersection_study.build_study, key)
        if study is None:
            raise ValueError(f"Unknown intersection key {key!r}; use search_intersections")
        return study

    @mcp.tool(annotations=WRITE)
    async def estimate_incident_delay(key: Intersection, refresh: bool = False) -> dict:
        """Modeled extra seconds of delay per vehicle caused by one typical lane-blocking
        incident at this intersection (SUMO, ~15 s, cached in the database), plus the share
        of incidents with no stated cause."""
        from app.infra.simulation import SumoSimulator  # needs eclipse-sumo installed

        estimate = await _run(
            intersection_study.estimate_incident_delay, key, SumoSimulator(), refresh
        )
        if estimate is None:
            raise ValueError(f"Unknown intersection key {key!r}; use search_intersections")
        return estimate

    @mcp.tool(annotations=READ)
    async def list_simulation_runs(limit: Annotated[int, Field(ge=1, le=100)] = 10) -> dict:
        """Recent simulation studies stored in the database: scenario, recommended option,
        lowest-delay option, decision explanation and evidence summary."""
        runs = await _run(disruptions.store().list_sims, limit)
        return {"runs": runs}

    @mcp.tool(annotations=READ)
    async def get_simulation_run(run_id: str) -> dict:
        """One stored study with its full action log, every option tested and every SUMO
        trial (seed, condition, metrics)."""
        run = await _run(disruptions.store().get_sim, run_id)
        if run is None:
            raise ValueError(f"Unknown simulation run {run_id!r}; use list_simulation_runs")
        return run

    @mcp.tool(annotations=WRITE)
    async def collect_latest_data(include_archive: bool = True) -> dict:
        """Poll the City now and append to the database (live incidents, closures, travel
        times, new archive incidents). Returns per-dataset inserted/updated counts."""
        if os.environ.get("BB_MCP_ALLOW_COLLECT", "1") == "0":
            raise PermissionError("Collection disabled on this server (BB_MCP_ALLOW_COLLECT=0)")
        return await _run(disruptions.collect_now, include_archive)

    @mcp.custom_route("/mcp-info", methods=["GET"])
    async def mcp_info(request: Request) -> JSONResponse:
        """Self-description: every tool with its schema; ?check=true runs a live self-test."""
        return JSONResponse(await describe(mcp, request.query_params.get("check") == "true"))

    return mcp


# Read-only tools that are safe and fast to exercise; the others write, call SUMO (~15 s)
# or fetch from the City API, so they are described but not executed by the self-check.
def _check_args(key):
    return {
        "get_disruption_summary": {},
        "get_data_status": {},
        "get_prediction_options": {"route": "Deerfoot Trail"},
        "search_intersections": {"limit": 3},
        "get_intersection_details": {"key": key},
        "predict_disruptions": {"route": "Stoney Trail", "horizon_days": 7, "save": False},
        "query_incident_history": {"limit": 3},
        "get_travel_time_history": {"limit": 3},
        "build_intersection_study": {"key": key},
        "list_simulation_runs": {"limit": 3},
    }


NOT_SELF_CHECKED = {
    "estimate_incident_delay": "runs SUMO (~15 s) and writes a cached estimate",
    "get_live_disruptions": "calls the City API and stores what it sees",
    "collect_latest_data": "polls the City API and writes to the database",
    "get_simulation_run": "needs a run id (use list_simulation_runs)",
}


async def describe(mcp, check=False):
    tools = await mcp.list_tools()
    results = {}
    if check:
        key = (await _run(disruptions.list_intersections, "", "", "", "incidents", 1))["items"][0][
            "key"
        ]
        for name, args in _check_args(key).items():
            started = time.perf_counter()
            try:
                await mcp.call_tool(name, args)
                results[name] = {
                    "status": "ok",
                    "ms": round((time.perf_counter() - started) * 1000),
                }
            except Exception as error:  # noqa: BLE001 - reported, not raised
                results[name] = {"status": "error", "error": f"{type(error).__name__}: {error}"}
        for name, why in NOT_SELF_CHECKED.items():
            results[name] = {"status": "not_run", "reason": why}
    catalog = []
    for t in tools:
        a = t.annotations
        props = (t.inputSchema or {}).get("properties", {})
        catalog.append(
            {
                "name": t.name,
                "description": " ".join((t.description or "").split()),
                "read_only": bool(a and a.readOnlyHint),
                "open_world": bool(a and a.openWorldHint),
                "arguments": {
                    k: {
                        "type": v.get("type") or [x.get("type") for x in v.get("anyOf", [])],
                        "default": v.get("default"),
                        "description": v.get("description"),
                        "enum": v.get("enum"),
                    }
                    for k, v in props.items()
                },
                **({"self_check": results[t.name]} if t.name in results else {}),
            }
        )
    settings = mcp.settings
    return {
        "server": {"name": mcp.name, "sdk": f"mcp {_mcp_version()}"},
        "endpoint": {
            "path": settings.streamable_http_path,
            "transport": "streamable-http (stateless)"
            if settings.stateless_http
            else "streamable-http",
            "host": settings.host,
            "port": settings.port,
            "agentcore_compatible": settings.stateless_http and settings.port == 8000,
        },
        "instructions": INSTRUCTIONS,
        "tools": catalog,
        "summary": {
            "tools": len(catalog),
            "read_only": sum(t["read_only"] for t in catalog),
            "writes": sum(not t["read_only"] for t in catalog),
            **(
                {
                    "self_check_ok": sum(r["status"] == "ok" for r in results.values()),
                    "self_check_errors": sum(r["status"] == "error" for r in results.values()),
                    "self_check_not_run": sum(r["status"] == "not_run" for r in results.values()),
                }
                if check
                else {}
            ),
        },
        "connect": {
            "claude_code": "claude mcp add --transport http calgary-disruptions "
            f"http://{settings.host}:{settings.port}{settings.streamable_http_path}",
            "inspector": "npx @modelcontextprotocol/inspector (Streamable HTTP)",
            "python_example": "scripts/mcp_client_demo.py",
        },
        "data": await _run(
            lambda: {
                k: v
                for k, v in disruptions.status().items()
                if k in ("incidents", "closures", "simulation_runs", "last_run_utc", "db_path")
            }
        ),
    }


def _mcp_version():
    import importlib.metadata as md

    return md.version("mcp")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    http = args.transport == "streamable-http"
    build_server(args.host, args.port, stateless=http).run(transport=args.transport)


if __name__ == "__main__":
    main()
