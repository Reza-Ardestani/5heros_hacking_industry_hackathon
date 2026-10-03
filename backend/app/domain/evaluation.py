"""Constraints, Pareto dominance and explicit hypothetical economics."""

import math
from statistics import mean


def compare(candidate: dict, reference: dict, budget: float, guardrail: float) -> dict:
    reasons, details = [], []
    if candidate["capital_cost_cad"] > budget:
        reasons.append("Exceeds capital budget")
        details.append(
            {
                "rule": "budget",
                "setting": "budget_cad",
                "observed": candidate["capital_cost_cad"],
                "limit": budget,
                "message": f"Capital ${candidate['capital_cost_cad']:,.0f} exceeds the "
                f"${budget:,.0f} budget",
            }
        )
    if candidate["metrics"]["unserved"] or reference["metrics"]["unserved"]:
        reasons.append("Incomplete trips: horizon-censored comparison, no effectiveness claim")
        details.append(
            {
                "rule": "complete_trips",
                "setting": None,
                "observed": candidate["metrics"]["unserved"],
                "limit": 0,
                "message": "Some trips did not finish in the simulated horizon, so the "
                "comparison is censored",
            }
        )
    base_cross = reference["metrics"]["cross_mean_delay_s"]
    # One second floor avoids division by zero when reference has near-zero delay.
    cross_change = (
        100 * (candidate["metrics"]["cross_mean_delay_s"] - base_cross) / max(1, base_cross)
    )
    if cross_change > guardrail:
        reasons.append("Exceeds cross-street delay guardrail")
        details.append(
            {
                "rule": "cross_street",
                "setting": "cross_guardrail_pct",
                "observed": round(cross_change, 2),
                "limit": guardrail,
                "message": f"Cross-street delay +{cross_change:.0f}% exceeds the "
                f"{guardrail:g}% limit",
            }
        )
    baseline_delay = reference["metrics"]["total_delay_s"]
    gain = baseline_delay - candidate["metrics"]["total_delay_s"]
    return {
        "feasible": not reasons,
        "rejection_reasons": reasons,
        "rejection_details": details,
        "delay_reduction_pct": 100 * gain / max(1, baseline_delay),
        "vehicle_hours_saved": gain / 3600,
        "cross_delay_change_pct": cross_change,
    }


def explain_decision(rows: list[dict], recommended_id: str) -> dict:
    """Why the recommendation won, which option has the lowest delay overall, and which
    setting change would make a lower-delay rejected option eligible."""
    by_id = {r["id"]: r for r in rows}
    recommended = by_id[recommended_id]
    lowest = min(rows, key=lambda r: r["metrics"]["total_delay_s"])
    better_rejected = [
        r
        for r in rows
        if not r["comparison"]["feasible"]
        and r["metrics"]["total_delay_s"] < recommended["metrics"]["total_delay_s"]
    ]
    changes = []
    for r in sorted(better_rejected, key=lambda r: r["metrics"]["total_delay_s"]):
        fixable = [d for d in r["comparison"]["rejection_details"] if d["setting"]]
        blocked = [d for d in r["comparison"]["rejection_details"] if not d["setting"]]
        if blocked:
            changes.append({"id": r["id"], "label": r["label"], "possible": False,
                            "reason": blocked[0]["message"], "settings": []})  # fmt: skip
            continue
        settings = [
            {
                "setting": d["setting"],
                "needed": math.ceil(d["observed"]) + (1 if d["rule"] == "cross_street" else 0),
                "current": d["limit"],
                "message": d["message"],
            }
            for d in fixable
        ]
        changes.append({"id": r["id"], "label": r["label"], "possible": True,
                        "delay_s_per_vehicle": r["metrics"]["mean_delay_s"],
                        "settings": settings})  # fmt: skip
    return {
        "rule": "Lowest total modeled delay among options that pass every study rule "
        "(budget, cross-street limit, complete trips)",
        "recommended_id": recommended_id,
        "lowest_delay_id": lowest["id"],
        "lowest_delay_is_recommended": lowest["id"] == recommended_id,
        "lowest_delay_rejected_because": [
            d["message"] for d in lowest["comparison"].get("rejection_details", [])
        ],
        "what_would_change": changes,
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
