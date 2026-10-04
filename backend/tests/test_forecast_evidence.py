from copy import deepcopy
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.application import disruptions
from app.application.assistant import Assistant
from app.domain import forecast


@pytest.mark.parametrize("requested", ["auto", "flat", "bayes", "lightgbm"])
def test_api_evidence_matches_actual_model_not_automatic_winner(requested):
    response = TestClient(app).get("/api/disruptions/predict", params={"model": requested})
    assert response.status_code == 200
    prediction = response.json()
    bt, evaluation = prediction["backtest"], prediction["forecast_evaluation"]
    actual = prediction["model"]["name"]
    assert actual == (bt["selected_model"] if requested == "auto" else requested)
    assert evaluation["model"] == actual
    score = bt["models"][actual]
    assert evaluation["model_daily_mae"] == score["test_daily_mae"]
    assert evaluation["model_expected_test_incidents"] == score["test_expected"]
    assert evaluation["interval_80_coverage_pct"] == score["test_interval_80_coverage_pct"]
    assert evaluation["test_start"] == bt["test_start"]
    assert evaluation["improvement_vs_baseline_pct"] == round(
        100 * (1 - score["test_daily_mae"] / bt["baseline_daily_mae"]), 1
    )
    assert bt["model_daily_mae"] == bt["models"][bt["selected_model"]]["test_daily_mae"]
    if requested == "flat":
        assert evaluation["improvement_vs_baseline_pct"] == 0


def history(monkeypatch, length, incident_days):
    days = [date(2026, 4, 1) + timedelta(i) for i in range(length)]
    times = [datetime.combine(days[i], datetime.min.time()) for i in incident_days]
    data = {
        "observed_days": days,
        "forecast_start": days[-1] + timedelta(1),
        "city_times": times,
        "incidents": [
            {
                "start_local": t.isoformat(),
                "intersection_key": "",
                "lane_impact_level": 0,
                "category": "Other",
            }
            for t in times
        ],
    }
    monkeypatch.setattr(disruptions, "_load", lambda: data)


def test_forecast_eligible_only_on_full_history_has_no_substitute_evidence(monkeypatch):
    # 35 incidents arrive after the shortest validation fold: trees can forecast,
    # but have no comparable historical test score under this protocol.
    history(monkeypatch, 140, range(105, 140))
    prediction = disruptions.predict(model_name="lightgbm")
    assert prediction["model"]["name"] == "lightgbm"
    assert "lightgbm" not in prediction["backtest"]["models"]
    assert prediction["forecast_evaluation"] is None


def test_fallback_evidence_uses_bayes_and_short_history_is_unavailable(monkeypatch):
    history(monkeypatch, 140, [1, 20, 50, 80, 120])
    prediction = disruptions.predict(model_name="lightgbm")
    assert prediction["model"]["requested"] == "lightgbm"
    assert prediction["model"]["name"] == prediction["forecast_evaluation"]["model"] == "bayes"
    assert prediction["model"]["note"]
    history(monkeypatch, 14, [1, 3, 10])
    prediction = disruptions.predict(model_name="flat")
    assert prediction["backtest"] is None and prediction["forecast_evaluation"] is None


def test_zero_error_baseline_and_projection_do_not_change_selection(monkeypatch):
    history(monkeypatch, 140, range(140))
    prediction = disruptions.predict(model_name="flat")
    bt = prediction["backtest"]
    original = deepcopy(bt)
    evaluation = forecast.forecast_evaluation(bt, "flat")
    assert evaluation["baseline_daily_mae"] == 0
    assert evaluation["improvement_vs_baseline_pct"] is None
    assert bt == original


@pytest.mark.anyio
@pytest.mark.parametrize(
    "evaluation, expected",
    [
        (
            {"label": "LightGBM", "test_days": 28, "improvement_vs_baseline_pct": 9.1},
            "LightGBM had 9.1% lower error",
        ),
        (
            {"label": "LightGBM", "test_days": 28, "improvement_vs_baseline_pct": -4.2},
            "LightGBM had 4.2% higher error",
        ),
        (
            {"label": "Flat", "test_days": 28, "improvement_vs_baseline_pct": 0},
            "Flat had the same error as the flat baseline",
        ),
        (None, "No comparable held-out evaluation"),
        (
            {"label": "LightGBM", "test_days": 28, "improvement_vs_baseline_pct": None},
            "baseline has zero error",
        ),
    ],
)
async def test_assistant_does_not_attribute_auto_winner_to_forced_model(
    monkeypatch, evaluation, expected
):
    monkeypatch.setenv("BB_CHAT_MODE", "builtin")
    assistant = Assistant()
    monkeypatch.setattr(assistant, "find_route", lambda _: None)

    async def call(*args):
        return {
            "model": {"name": "lightgbm"},
            "expected_total": 143,
            "interval_80": [100, 180],
            "backtest": {"test_days": 28, "improvement_vs_baseline_pct": 10.8},
            "forecast_evaluation": evaluation,
            "caveat": "Reported incidents only.",
        }

    monkeypatch.setattr(assistant, "call", call)
    reply = await assistant._predict("forecast with lightgbm", " lightgbm ", "", None, [])
    assert expected in reply["reply"]
    assert "10.8%" not in reply["reply"]
