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


def test_negative_binomial_interval_widens_with_dispersion():
    assert forecast.nb_interval(20, 0) == forecast.poisson_interval(20)
    lo_p, hi_p = forecast.poisson_interval(20)
    lo, hi = forecast.nb_interval(20, 0.15)  # Var = 20 + 0.15 * 400 = 80, vs 20
    assert lo < lo_p and hi > hi_p and lo < 20 < hi
    assert forecast.nb_interval(0, 0.15) == (0, 0)
    assert forecast.p_at_least_one(2, 0.15) < forecast.p_at_least_one(2, 0)


def test_dispersion_separates_steady_from_bursty_history():
    # Same weekly mean (two per weekday); bursty alternates zero and four.
    days, steady = _history(140, lambda d: [7, 8] if d.weekday() < 5 else [])
    _, bursty = _history(
        140, lambda d: ([7, 8, 9, 10] if (d - days[0]).days % 14 < 7 else []) * (d.weekday() < 5)
    )
    assert forecast.dispersion(steady, days) == 0
    # Weekday mean 2, counts 0 or 4: ((4 - 2)^2 - 2) / 2^2 = 0.5 exactly.
    assert abs(forecast.dispersion(bursty, days) - 0.5) < 1e-9
    out = forecast.forecast(bursty, days, bursty, days[-1] + timedelta(1), 7)
    lo, hi = forecast.poisson_interval(out["expected_total"])
    assert out["dispersion"] == 0.5
    assert out["interval_80"][1] - out["interval_80"][0] > hi - lo


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


def test_recent_shift_cancels_citywide_shocks_and_fdr_controls_screening():
    # Slice holds 15% of the city's recent-window share; city share is 15%: no change.
    assert forecast.recent_shift(15, 100, 0.15)["p_value"] > 0.5
    surge = forecast.recent_shift(40, 100, 0.15)
    assert surge["direction"] == "rising" and surge["ratio"] > 2 and surge["p_value"] < 1e-6
    assert forecast.recent_shift(0, 100, 0.15)["direction"] == "falling"
    # One strong signal among many null p-values survives; borderline ones do not.
    assert forecast.benjamini_hochberg([1e-6] + [0.04] * 3 + [0.5] * 96) == [True] + [False] * 99


def test_priorities_rank_corridors_with_checked_forecast_statistics():
    client = TestClient(app)
    r = client.get("/api/disruptions/priorities", params={"horizon_days": 14}).json()
    items, a = r["items"], r["analysis"]
    assert r["level"] == "corridor" and r["horizon_days"] == 14 and 0 < len(items) <= 15
    assert [i["expected"] for i in items] == sorted((i["expected"] for i in items), reverse=True)
    for i in items:
        assert i["interval_80"][0] <= i["expected"] <= i["interval_80"][1]
        assert i["history_incidents"] >= r["min_incidents"]
        assert 0 <= i["expected_lane_blocking"] <= i["expected"]
        assert i["trend"] in {"rising", "falling", "steady"}
    assert not set(a["rising"]) & set(a["falling"])
    assert 0 < a["top_share_of_citywide_pct"] < 100
    check = a["ranking_check"]
    assert check and 0 <= check["forecast"]["overlap_with_actual_top"] <= check["top_n"]
    lane = client.get("/api/disruptions/priorities", params={"sort": "lane_blocking"}).json()
    values = [i["expected_lane_blocking"] for i in lane["items"]]
    assert values == sorted(values, reverse=True)
    spots = client.get("/api/disruptions/priorities", params={"level": "intersection"}).json()
    assert spots["level"] == "intersection" and all(" & " in i["key"] for i in spots["items"])
    assert all(i["corridor"] for i in spots["items"])


def test_priority_study_spot_is_a_hotspot_the_arterial_model_can_represent():
    client = TestClient(app)
    items = client.get("/api/disruptions/priorities", params={"limit": 100}).json()["items"]
    with_spot = [i for i in items if i["study_spot"]]
    assert with_spot and len(with_spot) < len(items)  # freeway-only corridors get none
    for i in with_spot[:5]:
        assert i["study_spot_incidents"] >= 5
        study = client.get(
            "/api/disruptions/intersection/study", params={"key": i["study_spot"]}
        ).json()
        assert not any("exceeds the synthetic arterial" in w for w in study["warnings"])
