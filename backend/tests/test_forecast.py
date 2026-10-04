from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from app.api import app
from app.domain import forecast


def _history(days, per_day_hours):
    start = date(2026, 4, 1)
    out = []
    for i in range(days):
        d = start + timedelta(i)
        out += [datetime.fromisoformat(f"{d}T{h:02d}:00") for h in per_day_hours(d)]
    return [start + timedelta(i) for i in range(days)], out


def test_weekday_pattern_is_learned_and_beats_flat_baseline():
    # Weekdays: two AM-peak incidents; weekends: none.
    days, times = _history(140, lambda d: [7, 8] if d.weekday() < 5 else [])
    rates = forecast.fit(times, days, times, prior_weeks=0)
    assert rates[(0, 1)] == 2 and rates[(5, 1)] == 0 and rates[(0, 0)] == 0
    result = forecast.backtest(times, days, times)
    assert result["model_daily_mae"] < result["baseline_daily_mae"]
    out = forecast.forecast(times, days, times, days[-1] + timedelta(1), 7)
    assert abs(out["expected_total"] - 10) < 1e-6 and len(out["days"]) == 7


def test_poisson_interval_brackets_mean():
    lo, hi = forecast.poisson_interval(10)
    assert lo < 10 < hi and forecast.poisson_interval(0) == (0, 0)


def test_predict_endpoint_slices_and_intersection_overrides_route():
    client = TestClient(app)
    options = client.get("/api/disruptions/options").json()
    route = options["routes"][0]["value"]
    lanes = client.get("/api/disruptions/options", params={"route": route}).json()["lanes"]
    assert lanes and options["max_horizon_days"] == 28
    whole = client.get("/api/disruptions/predict", params={"horizon_days": 7}).json()
    part = client.get("/api/disruptions/predict", params={"route": route}).json()
    assert part["history"]["incidents"] < whole["history"]["incidents"]
    assert whole["interval_80"][0] <= whole["expected_total"] <= whole["interval_80"][1]
    assert whole["backtest"]["baseline"] == forecast.BASELINE
    spot = client.get("/api/disruptions/intersections", params={"limit": 1}).json()["items"][0]
    alone = client.get("/api/disruptions/predict", params={"intersection": spot["key"]}).json()
    both = client.get(
        "/api/disruptions/predict", params={"intersection": spot["key"], "route": "nowhere"}
    ).json()
    assert alone["history"]["incidents"] == both["history"]["incidents"] == spot["incidents"]
    assert (
        client.get("/api/disruptions/predict", params={"horizon_days": 99}).json()["horizon_days"]
        == 28
    )
