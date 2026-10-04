from fastapi.testclient import TestClient

from app.api import app
from app.application import disruptions, intersection_study
from app.application.planner import PlanningService
from app.application.study_service import StudyService
from app.domain.models import IncidentSpec, Scenario
from app.infra.simulation import SumoSimulator


def _top_key():
    return disruptions.list_intersections(limit=1)["items"][0]["key"]


def test_study_is_derived_from_intersection_data_with_stated_assumptions():
    key = _top_key()
    study = TestClient(app).get("/api/disruptions/intersection/study", params={"key": key}).json()
    scenario = Scenario(**study["scenario"])  # validates
    e = study["evidence"]
    assert e["incidents"] == disruptions.intersection_detail(key)["incidents"]
    assert 0 <= e["unspecified_pct"] <= 100 and e["weekday_peak_periods"] > 0
    assert scenario.incident and 0 <= scenario.incident_weight <= 1
    assert scenario.incident_weight == round(
        min(1, e["peak_lane_blocking"] / e["weekday_peak_periods"]), 4
    )
    assert any("peak hour" in a for a in study["assumptions"])
    assert set(scenario.extra_options) == set(intersection_study.ALL_OPTIONS)


def test_scenario_validation_rejects_inconsistent_study_features():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Scenario(incident=IncidentSpec(lanes_blocked=2), arterial_lanes=1)
    with pytest.raises(ValidationError):
        Scenario(extra_options=["turn_ban"], turn_share=0)
    with pytest.raises(ValidationError):
        Scenario(extra_options=["incident_clearance"])


def test_all_new_options_run_in_sumo_with_weighted_conditions_and_summary():
    events = []
    scenario = Scenario(
        duration_s=300, main_vph=800, cross_vph=120, arterial_lanes=2, turn_share=0.15,
        incident=IncidentSpec(duration_s=240, start_s=60), incident_weight=0.25,
        extra_options=["signal_control", "incident_clearance", "turn_lane", "turn_ban"],
    )  # fmt: skip
    context = {"intersection_key": "Test & Junction SW", "evidence": {
        "incidents": 10, "observed_days": 184, "per_month": 1.6, "lane_blocking": 6,
        "lane_blocking_pct": 60, "peak_lane_blocking": 3, "unspecified": 4,
        "unspecified_pct": 40, "collisions": 2, "vulnerable_road_user": 0, "signal_faults": 1,
        "weekday_peak_periods": 264, "live_now": None}}  # fmt: skip
    result = StudyService(PlanningService(SumoSimulator())).run(scenario, events.append, context)
    ids = [a["id"] for a in result["alternatives"]]
    assert ids == ["reference", "candidate", "revised", "capacity", "signal_control",
                   "incident_clearance", "turn_lane", "turn_ban"]  # fmt: skip
    by_id = {a["id"]: a for a in result["alternatives"]}
    for alt in result["alternatives"]:
        assert set(alt["metrics_by_condition"]) == {"normal", "incident"}
        assert len(alt["holdout_trials"]) == 6
        normal, incident = (
            alt["metrics_by_condition"]["normal"],
            alt["metrics_by_condition"]["incident"],
        )
        expected = 0.75 * normal["total_delay_s"] + 0.25 * incident["total_delay_s"]
        assert abs(alt["metrics"]["total_delay_s"] - expected) < 1e-6
    # Clearance only changes incident conditions; its normal-condition trials match the reference.
    assert (
        by_id["incident_clearance"]["metrics_by_condition"]["normal"]
        == by_id["reference"]["metrics_by_condition"]["normal"]
    )
    assert (
        by_id["incident_clearance"]["metrics_by_condition"]["incident"]["total_delay_s"]
        < by_id["reference"]["metrics_by_condition"]["incident"]["total_delay_s"]
    )
    assert by_id["turn_ban"]["holdout_trials"][0]["metrics"]["turn_detour_penalty_s"] > 0
    assert result["incident_impact"]["extra_delay_s_per_vehicle"] > 0
    summary = result["evidence_summary"]
    assert summary["intersection_key"] == "Test & Junction SW"
    assert len(summary["options"]) == 7 and summary["observed_facts"]
    assert any(e["action"] == "evidence_summary" for e in events)
