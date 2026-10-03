import json

import pytest

mcp = pytest.importorskip("mcp", reason="install with: uv sync --group mcp")

from mcp.shared.memory import create_connected_server_and_client_session

from app.mcp_server import build_server

EXPECTED = {
    "get_disruption_summary", "get_prediction_options", "search_intersections",
    "get_intersection_details", "predict_disruptions", "query_incident_history",
    "get_travel_time_history", "get_live_disruptions", "get_data_status", "collect_latest_data",
    "build_intersection_study", "estimate_incident_delay", "list_simulation_runs",
    "get_simulation_run",
}  # fmt: skip


def _payload(result):
    assert not result.isError, result.content
    return json.loads(result.content[0].text)


@pytest.mark.anyio
async def test_tools_are_listed_and_callable(seeded_store):
    server = build_server()._mcp_server
    async with create_connected_server_and_client_session(server) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
        assert set(tools) == EXPECTED
        assert tools["get_disruption_summary"].annotations.readOnlyHint is True
        assert tools["collect_latest_data"].annotations.readOnlyHint is False
        assert "horizon_days" in tools["predict_disruptions"].inputSchema["properties"]

        summary = _payload(await client.call_tool("get_disruption_summary", {}))
        assert summary["headline"]["incidents"] > 0 and "caveat" in summary

        options = _payload(await client.call_tool("get_prediction_options", {}))
        route = options["routes"][0]["value"]
        before = seeded_store.stats()["predictions_saved"]
        forecast = _payload(
            await client.call_tool("predict_disruptions", {"route": route, "horizon_days": 3})
        )
        assert len(forecast["days"]) == 3 and forecast["backtest"]["baseline"]
        assert seeded_store.stats()["predictions_saved"] == before + 1

        top = _payload(await client.call_tool("search_intersections", {"limit": 1}))["items"][0]
        detail = _payload(await client.call_tool("get_intersection_details", {"key": top["key"]}))
        assert detail["incidents"] == top["incidents"]
        bad = await client.call_tool("get_intersection_details", {"key": "nowhere"})
        assert bad.isError

        history = _payload(
            await client.call_tool("query_incident_history", {"route": route, "limit": 2})
        )
        assert history["returned"] == 2
        status = _payload(await client.call_tool("get_data_status", {}))
        assert status["incidents"] > 0
        study = _payload(await client.call_tool("build_intersection_study", {"key": top["key"]}))
        assert study["scenario"]["extra_options"] and study["assumptions"]
        runs = _payload(await client.call_tool("list_simulation_runs", {}))
        assert isinstance(runs["runs"], list)


@pytest.fixture
def anyio_backend():
    return "asyncio"
