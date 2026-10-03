"""Constraints, Pareto dominance and explicit hypothetical economics."""

from statistics import mean


def compare(candidate: dict, reference: dict, budget: float, guardrail: float) -> dict:
    reasons = []
    if candidate["capital_cost_cad"] > budget:
        reasons.append("Exceeds capital budget")
    if candidate["metrics"]["unserved"] or reference["metrics"]["unserved"]:
        reasons.append("Incomplete trips: horizon-censored comparison, no effectiveness claim")
    base_cross = reference["metrics"]["cross_mean_delay_s"]
    # One second floor avoids division by zero when reference has near-zero delay.
    cross_change = (
        100 * (candidate["metrics"]["cross_mean_delay_s"] - base_cross) / max(1, base_cross)
    )
    if cross_change > guardrail:
        reasons.append("Exceeds cross-street delay guardrail")
    baseline_delay = reference["metrics"]["total_delay_s"]
    gain = baseline_delay - candidate["metrics"]["total_delay_s"]
    return {
        "feasible": not reasons,
        "rejection_reasons": reasons,
        "delay_reduction_pct": 100 * gain / max(1, baseline_delay),
        "vehicle_hours_saved": gain / 3600,
        "cross_delay_change_pct": cross_change,
    }


def pareto(candidates: list[dict]) -> list[str]:
    feasible = [c for c in candidates if c["comparison"]["feasible"]]

    def dominates(a, b):
        ac, bc = a["capital_cost_cad"], b["capital_cost_cad"]
        ad, bd = a["metrics"]["total_delay_s"], b["metrics"]["total_delay_s"]
        return ac <= bc and ad <= bd and (ac < bc or ad < bd)

    return [c["id"] for c in feasible if not any(dominates(o, c) for o in feasible)]


def economics(hours_saved: float, cost: float, scenario) -> dict:
    benefit = (
        hours_saved * scenario.occupancy * scenario.value_of_time_cad * scenario.operating_days
    )
    operating = scenario.annual_operating_cost_cad if cost > 0 else 0
    annualized = cost / scenario.asset_life_years + operating
    return {
        "estimated_annual_time_value_cad": round(benefit, 2),
        "estimated_annualized_cost_cad": round(annualized, 2),
        "estimated_net_annual_value_cad": round(benefit - annualized, 2),
        "label": "Illustrative undiscounted annualization of this modeled period; not field savings",
    }


def aggregate(samples: list[dict]) -> dict:
    keys = (
        "total_delay_s",
        "mean_delay_s",
        "main_mean_delay_s",
        "cross_mean_delay_s",
        "mean_trip_s",
        "max_queue",
        "completed",
        "unfinished",
        "uninserted",
        "unserved",
        "planned",
        "departure_delay_s",
    )
    return {key: mean(s[key] for s in samples) for key in keys}
