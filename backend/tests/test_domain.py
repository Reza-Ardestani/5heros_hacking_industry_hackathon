import pytest
from pydantic import ValidationError

from app.domain.evaluation import compare, cost_stress, economics, pareto
from app.domain.models import Scenario
from app.infra.simulation import make_demand


@pytest.mark.parametrize(
    "inputs",
    [
        {"main_vph": -1},
        {"main_vph": float("nan")},
        {"budget_cad": float("inf")},
        {"duration_s": 9999},
    ],
)
def test_invalid_inputs(inputs):
    with pytest.raises(ValidationError):
        Scenario(**inputs)


def test_measured_profile_requires_provenance_and_complete_intervals():
    with pytest.raises(ValidationError):
        Scenario(demand_kind="measured")
    with pytest.raises(ValidationError):
        Scenario(flow_profile=[{"begin_s": 10, "end_s": 900, "main_vph": 300, "cross_vph": 80}])
    accepted = Scenario(
        demand_kind="measured",
        demand_source="Public study URL; 2026-09-01",
        flow_profile=[{"begin_s": 0, "end_s": 900, "main_vph": 300, "cross_vph": 80}],
    )
    assert accepted.average_flows() == (300, 80)


def row(name, delay, cross=20, cost=0, unserved=0):
    return {
        "id": name,
        "capital_cost_cad": cost,
        "metrics": {"total_delay_s": delay, "cross_mean_delay_s": cross, "unserved": unserved},
    }


def test_budget_guardrail_and_censored_comparison_rejections():
    base = row("base", 1000)
    assert not compare(row("expensive", 500, cost=100001), base, 100000, 30)["feasible"]
    assert not compare(row("unfair", 500, cross=30), base, 100000, 30)["feasible"]
    assert not compare(row("unfinished", 500, unserved=1), base, 100000, 30)["feasible"]
    good = compare(row("balanced", 700, cross=24, cost=15000), base, 100000, 30)
    assert good["feasible"] and good["delay_reduction_pct"] == 30


def test_pareto_preserves_cost_tradeoff_and_excludes_dominated():
    candidates = [
        row("reference", 1000),
        row("retime", 700, cost=15000),
        row("worse", 800, cost=20000),
        row("capacity", 400, cost=1200000),
    ]
    for candidate in candidates:
        candidate["comparison"] = {"feasible": True}
    assert pareto(candidates) == ["reference", "retime", "capacity"]


def test_economic_units_and_reference_has_no_operating_cost():
    scenario = Scenario(
        occupancy=2,
        value_of_time_cad=20,
        operating_days=200,
        asset_life_years=10,
        annual_operating_cost_cad=2000,
    )
    value = economics(10, 100000, scenario)
    assert value["estimated_annual_time_value_cad"] == 80000
    assert value["estimated_net_annual_value_cad"] == 68000
    assert economics(0, 0, scenario)["estimated_annualized_cost_cad"] == 0


def test_fixed_demand_is_repeatable_and_stress_changes_arrivals():
    scenario = Scenario()
    assert make_demand(scenario, 42) == make_demand(scenario, 42)
    assert make_demand(scenario, 42) != make_demand(scenario, 43)
    assert len(make_demand(scenario, 42, 0.8)) < len(make_demand(scenario, 42, 1.2))


def _decided(rows, budget=100000, guardrail=30):
    for r in rows:
        r.setdefault("label", r["id"].replace("_", " ").title())
        r["comparison"] = compare(r, rows[0], budget, guardrail)
    return rows


def test_cost_stress_finds_robust_and_fragile_recommendations():
    scenario = Scenario(budget_cad=100000, cross_guardrail_pct=30)
    rows = _decided([
        row("reference", 1000),
        row("retime", 700, cost=15000),
        row("unfair", 300, cross=40, cost=5000),
        row("capacity", 400, cost=1200000),
    ])  # fmt: skip
    robust = cost_stress(rows, "retime", scenario)
    assert robust["robust_share_pct"] == 100 and robust["verdict"].startswith("Robust")
    assert robust["headroom"]["cost_increase_pct"] == pytest.approx(566.7)
    assert robust["headroom"]["fallback_id"] == "reference"
    assert [s["id"] for s in robust["switch_points"]] == ["capacity"]
    assert [b["id"] for b in robust["blocked"]] == ["unfair"]  # no cost change can fix it
    assert robust["economics"]["worst_case_net_cad"] < robust["economics"]["net_annual_value_cad"]

    # A lower-delay option just over budget: +25% budget makes it win.
    fragile_rows = _decided([
        row("reference", 1000),
        row("retime", 700, cost=15000),
        row("turn_lane", 500, cost=120000),
    ])  # fmt: skip
    fragile = cost_stress(fragile_rows, "retime", scenario)
    assert fragile["robust_share_pct"] < 100
    assert fragile["switch_points"][0]["budget_increase_pct"] == 20
    assert fragile["grid"][3][2] == "turn_lane"  # budget +20% (= $120k), costs unchanged
    assert fragile["grid"][3][3] == "retime"  # ...but not if costs also rise 20%
    assert fragile["grid"][0][2] == "retime"
    assert {c["id"] for c in fragile["one_at_a_time"]} == {"turn_lane"}
    assert "+20%" in fragile["verdict"]
