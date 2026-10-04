#!/usr/bin/env python3
"""Connect to the Calgary disruption MCP server like an agent would, and call its tools.

Start the server first (repository root):
    make mcp-http          # serves http://127.0.0.1:8000/mcp (stateless streamable HTTP)
Then:
    cd backend && uv run --group mcp python ../scripts/mcp_client_demo.py [URL]
"""

import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/mcp"


async def call(session, tool, **arguments):
    result = await session.call_tool(tool, arguments)
    if result.isError:
        raise RuntimeError(result.content[0].text)
    return json.loads(result.content[0].text)


async def main():
    async with streamablehttp_client(URL) as (read, write, _), ClientSession(read, write) as s:
        info = await s.initialize()
        print(f"Connected to {info.serverInfo.name} at {URL}")
        tools = (await s.list_tools()).tools
        print(f"{len(tools)} tools: {', '.join(t.name for t in tools)}\n")

        status = await call(s, "get_data_status")
        print(
            f"1. get_data_status -> {status['incidents']} incidents, {status['closures']} "
            f"closures, {status['simulation_runs']} simulation runs in {status['db_path']}"
        )

        top = (await call(s, "search_intersections", limit=3))["items"]
        print(
            "2. search_intersections -> " + "; ".join(f"{i['key']} ({i['incidents']})" for i in top)
        )

        key = top[0]["key"]
        detail = await call(s, "get_intersection_details", key=key)
        est = detail.get("incident_delay_estimate") or {}
        print(
            f"3. get_intersection_details('{key}') -> {detail['collisions']} collisions, "
            f"{detail['unspecified_pct']}% unspecified, camera {detail['camera']['image_url']}, "
            f"incident delay +{est.get('extra_delay_s_per_vehicle', '?')} s/vehicle"
        )

        opts = await call(s, "get_prediction_options", route="Stoney Trail")
        print(
            f"4. get_prediction_options(route=Stoney Trail) -> lanes "
            f"{[o['value'] for o in opts['lanes'][:4]]}"
        )

        p = await call(s, "predict_disruptions", route="Stoney Trail", horizon_days=7, save=False)
        bt = p["backtest"]
        print(
            f"5. predict_disruptions(Stoney Trail, 7d) -> {p['expected_total']} expected "
            f"{p['interval_80']}, model {p['model']['name']} (chosen on validation); test MAE "
            + ", ".join(f"{k} {v['test_daily_mae']}" for k, v in bt["models"].items())
        )

        study = await call(s, "build_intersection_study", key=key)
        sc = study["scenario"]
        print(
            f"6. build_intersection_study -> {sc['main_vph']} veh/h, {sc['arterial_lanes']} lanes, "
            f"incident weight {sc['incident_weight']}, options {sc['extra_options']}"
        )

        live = await call(s, "get_live_disruptions")
        print(
            f"7. get_live_disruptions -> {len(live['incidents'])} live incidents, "
            f"{len(live['active_closures'])} active closures (persisted={live['persisted']})"
        )

        runs = (await call(s, "list_simulation_runs", limit=3))["runs"]
        for r in runs:
            print(
                f"8. list_simulation_runs -> {r['id'][:8]} {r['status']} "
                f"{r.get('intersection_key') or 'default study'} -> recommended {r['recommended_id']}"
            )


if __name__ == "__main__":
    asyncio.run(main())
