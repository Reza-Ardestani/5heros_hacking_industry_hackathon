import json

import pytest

mcp = pytest.importorskip("mcp", reason="install with: uv sync")

from mcp.shared.memory import create_connected_server_and_client_session

from app.mcp_server import build_server

EXPECTED = {
    "get_disruption_summary", "get_prediction_options", "search_intersections",
    "get_intersection_details", "predict_disruptions", "query_incident_history",
    "get_travel_time_history", "get_live_disruptions", "get_data_status", "collect_latest_data",
    "build_intersection_study", "estimate_incident_delay", "list_simulation_runs",
    "get_simulation_run", "rank_priorities",
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

        assert tools["rank_priorities"].annotations.readOnlyHint is True
        ranked = _payload(await client.call_tool("rank_priorities", {"limit": 3}))
        assert ranked["level"] == "corridor" and len(ranked["items"]) == 3
        assert ranked["analysis"]["ranking_check"] and "study_spot" in ranked["items"][0]


@pytest.mark.anyio
async def test_agent_initialization_and_forced_forecast_use_actual_model_evidence():
    server = build_server()._mcp_server
    async with create_connected_server_and_client_session(server) as client:
        initialized = await client.initialize()
        assert "quote forecast_evaluation for the actual forecast model" in initialized.instructions
        prediction = _payload(
            await client.call_tool("predict_disruptions", {"model": "flat", "save": False})
        )
        evaluation = prediction["forecast_evaluation"]
        assert prediction["model"]["name"] == evaluation["model"] == "flat"
        assert evaluation["improvement_vs_baseline_pct"] == 0
        assert (
            evaluation["model_daily_mae"]
            == prediction["backtest"]["models"]["flat"]["test_daily_mae"]
        )


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_mcp_info_describes_every_tool_and_self_checks_safe_ones(seeded_store):
    from app.mcp_server import NOT_SELF_CHECKED, describe

    server = build_server(port=8000, stateless=True)
    info = await describe(server, check=True)
    names = {t["name"] for t in info["tools"]}
    assert names == EXPECTED and info["summary"]["tools"] == len(EXPECTED)
    assert info["endpoint"]["path"] == "/mcp" and info["endpoint"]["agentcore_compatible"]
    assert info["summary"]["self_check_errors"] == 0
    statuses = {t["name"]: t["self_check"]["status"] for t in info["tools"]}
    assert all(statuses[n] == "not_run" for n in NOT_SELF_CHECKED)
    assert sum(s == "ok" for s in statuses.values()) == info["summary"]["self_check_ok"] == 11
