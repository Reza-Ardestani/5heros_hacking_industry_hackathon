from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.application import disruptions
from app.bootstrap import create_assistant
from app.infra.chat_model import chat_mode


@pytest.fixture
def builtin(monkeypatch):
    monkeypatch.setenv("BB_CHAT_MODE", "builtin")
    return create_assistant()


@pytest.mark.anyio
async def test_navigation_needs_no_tools(builtin):
    r = await builtin.reply("go to compare")
    assert r["actions"] == [{"type": "navigate", "view": "compare", "step": 4}]
    assert r["tools_used"] == [] and r["mode"] == "builtin"
    r = await builtin.reply("open the evidence page")
    assert r["actions"][0]["view"] == "evidence"
    r = await builtin.reply("show mcp info ml tab")
    assert r["actions"][0]["tab"] == "mcp-info-ml"


@pytest.mark.anyio
async def test_hotspots_use_search_and_open_the_top_one(builtin):
    r = await builtin.reply("top 3 hotspots in SE")
    assert r["tools_used"] == ["search_intersections"]
    top = disruptions.list_intersections("", "SE", "", "incidents", 1)["items"][0]
    assert r["actions"][0] == {
        "type": "navigate", "view": "intersections", "intersection": top["key"], "quadrant": "SE",
    }  # fmt: skip
    assert top["key"] in r["reply"]


@pytest.mark.anyio
async def test_named_intersection_opens_its_detail(builtin):
    item = disruptions.list_intersections("", "", "", "incidents", 1)["items"][0]
    roads = " and ".join(item["roads"])
    r = await builtin.reply(f"tell me about {roads}")
    assert r["tools_used"] == ["get_intersection_details"]
    assert r["actions"][0]["intersection"] == item["key"]
    assert str(item["incidents"]) in r["reply"]


@pytest.mark.anyio
async def test_forecast_matches_route_and_never_saves(builtin, seeded_store):
    route = disruptions.options("", "")["routes"][0]["value"]
    before = seeded_store.stats()["predictions_saved"]
    r = await builtin.reply(f"forecast {route} next 14 days with bayes")
    assert r["tools_used"] == ["predict_disruptions"]
    call = r["tool_calls"][0]["args"]
    assert call["route"] == route and call["horizon_days"] == 14 and call["model"] == "bayes"
    assert call["save"] is False
    assert seeded_store.stats()["predictions_saved"] == before
    assert r["actions"][0]["prediction"]["route"] == route
    assert "not measured flow" in r["reply"]  # caveat is passed on


@pytest.mark.anyio
async def test_simulate_returns_a_study_action(builtin):
    item = disruptions.list_intersections("", "", "", "incidents", 1)["items"][0]
    r = await builtin.reply("simulate " + " & ".join(item["roads"]))
    assert r["tools_used"] == ["build_intersection_study"]
    assert r["actions"] == [{"type": "study", "intersection": item["key"]}]


@pytest.mark.anyio
async def test_unknown_text_gets_help_and_suggestions(builtin):
    r = await builtin.reply("purple elephants")
    assert r["actions"] == [] and r["suggestions"]


def test_chat_endpoint(monkeypatch):
    monkeypatch.setenv("BB_CHAT_MODE", "builtin")
    client = TestClient(app)
    assert client.get("/api/chat/info").json()["mode"] == "builtin"
    r = client.post("/api/chat", json={"message": "data status", "history": []})
    assert r.status_code == 200 and r.json()["tools_used"] == ["get_data_status"]
    assert client.post("/api/chat", json={"message": ""}).status_code == 422


def test_mode_follows_key(monkeypatch):
    monkeypatch.delenv("BB_CHAT_MODE", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert chat_mode() == "builtin"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-a-key")
    assert chat_mode() == "claude"
    monkeypatch.setenv("BB_CHAT_MODE", "builtin")
    assert chat_mode() == "builtin"


class FakeMessages:
    """Scripted Claude: first asks for a search and a navigation, then answers."""

    def __init__(self, key, fail=False):
        self.key, self.fail, self.requests = key, fail, []

    async def create(self, **kwargs):
        self.requests.append(kwargs)
        if self.fail:
            raise RuntimeError("offline")
        if len(self.requests) == 1:
            return SimpleNamespace(
                stop_reason="tool_use",
                content=[
                    SimpleNamespace(
                        type="tool_use", id="t1", name="search_intersections", input={"limit": 1}
                    ),
                    SimpleNamespace(
                        type="tool_use",
                        id="t2",
                        name="navigate_ui",
                        input={"view": "intersections", "intersection": self.key},
                    ),
                ],
            )
        return SimpleNamespace(
            stop_reason="end_turn", content=[SimpleNamespace(type="text", text="Top: X.")]
        )


def _fake_client(monkeypatch, messages):
    import anthropic

    client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    monkeypatch.setattr(anthropic, "AsyncAnthropic", lambda: client)
    monkeypatch.setenv("BB_CHAT_MODE", "claude")


@pytest.mark.anyio
async def test_claude_mode_runs_mcp_tools_and_navigates(monkeypatch):
    key = disruptions.list_intersections("", "", "", "incidents", 1)["items"][0]["key"]
    fake = FakeMessages(key)
    _fake_client(monkeypatch, fake)
    r = await create_assistant().reply("busiest intersection?", [{"role": "assistant", "content": "hi"}])
    assert r["mode"] == "claude" and r["reply"] == "Top: X."
    assert r["tools_used"] == ["search_intersections"]
    assert r["actions"] == [{"type": "navigate", "view": "intersections", "intersection": key}]
    first = fake.requests[0]
    assert first["model"] == "claude-opus-5-5" and first["fallbacks"] == "default"
    assert first["messages"][0]["role"] == "user"  # leading assistant turn dropped
    names = {t["name"] for t in first["tools"]}
    assert "navigate_ui" in names and "collect_latest_data" not in names
    results = fake.requests[1]["messages"][-1]["content"]
    assert [x["tool_use_id"] for x in results] == ["t1", "t2"]  # one user turn, all results


@pytest.mark.anyio
async def test_claude_failure_falls_back_to_builtin(monkeypatch):
    _fake_client(monkeypatch, FakeMessages("", fail=True))
    r = await create_assistant().reply("go to compare")
    assert r["mode"] == "builtin" and "Claude unavailable" in r["notice"]
    assert r["actions"][0]["view"] == "compare"


@pytest.mark.anyio
async def test_budget_question_skips_provincial_roads_and_opens_a_study(builtin):
    r = await builtin.reply(
        "I have $5 million to spend on improving a road. Which road should I put it towards?"
    )
    assert r["tools_used"] == ["rank_priorities"]
    ranked = disruptions.priorities(limit=30)["items"]
    best = next(
        i for i in ranked if i["key"] not in {"Deerfoot Trail", "Stoney Trail"} and i["study_spot"]
    )
    assert r["actions"] == [{"type": "study", "intersection": best["study_spot"]}]
    assert r["reply"].startswith(f"{ranked[0]['key']} has the most reported disruption")
    assert f"Start with a study at {best['study_spot']}." in r["reply"]
    assert "$5,000,000" in r["reply"]
