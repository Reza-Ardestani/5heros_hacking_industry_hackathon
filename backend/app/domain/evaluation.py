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


COST_FACTORS = (0.5, 0.75, 1.0, 1.25, 1.5)
BUDGET_FACTORS = (0.5, 0.75, 1.0, 1.25, 1.5)
LEGACY_REASONS = {"budget": "budget", "guardrail": "cross_street", "Incomplete": "complete_trips"}


def _pick(rows: list[dict], costs: dict, budget: float, guardrail: float) -> str:
    """The planner's rule (lowest delay among options passing every check) at these costs."""
    reference = rows[0]
    eligible = [
        r
        for r in rows
        if compare({**r, "capital_cost_cad": costs[r["id"]]}, reference, budget, guardrail)[
            "feasible"
        ]
    ]
    if not eligible:
        return reference["id"]
    return min(eligible, key=lambda r: (r["metrics"]["total_delay_s"], costs[r["id"]]))["id"]


def cost_stress(rows: list[dict], recommended_id: str, scenario) -> dict:
    """Does the recommendation survive cost and budget uncertainty? No re-simulation needed:
    capital costs and the budget only enter the decision after the SUMO runs."""
    budget, guardrail = scenario.budget_cad, scenario.cross_guardrail_pct
    by_id = {r["id"]: r for r in rows}
    rec = by_id[recommended_id]
    base = {r["id"]: r["capital_cost_cad"] for r in rows}
    label = rec["label"]

    grid = [
        [_pick(rows, {k: c * cf for k, c in base.items()}, budget * bf, guardrail)
         for cf in COST_FACTORS]
        for bf in BUDGET_FACTORS
    ]  # fmt: skip
    cells = [w for row in grid for w in row]
    robust = sum(w == recommended_id for w in cells)

    one_at_a_time = []
    for r in rows[1:]:
        for f in (0.5, 1.5):
            winner = _pick(rows, {**base, r["id"]: base[r["id"]] * f}, budget, guardrail)
            if winner != recommended_id:
                one_at_a_time.append({"id": r["id"], "label": r["label"], "factor": f,
                                      "winner_id": winner, "winner": by_id[winner]["label"]})  # fmt: skip

    headroom = None
    if recommended_id != rows[0]["id"] and base[recommended_id] > 0:
        fallback = _pick(rows, {**base, recommended_id: math.inf}, budget, guardrail)
        headroom = {
            "cost_increase_pct": round(100 * (budget / base[recommended_id] - 1), 1),
            "min_budget_cad": base[recommended_id],
            "fallback_id": fallback,
            "fallback": by_id[fallback]["label"],
        }

    # Lower-delay options rejected only by the budget win once they fit within it.
    switch_points, blocked = [], []
    for r in sorted(rows, key=lambda r: r["metrics"]["total_delay_s"]):
        if r["metrics"]["total_delay_s"] >= rec["metrics"]["total_delay_s"]:
            break
        details = r["comparison"].get("rejection_details") or [
            # Results saved before rejection_details existed carry only reason strings.
            {"rule": rule, "message": reason}
            for reason in r["comparison"].get("rejection_reasons", [])
            for key, rule in LEGACY_REASONS.items()
            if key in reason
        ]
        rules = {d["rule"] for d in details}
        if rules == {"budget"}:
            switch_points.append({
                "id": r["id"], "label": r["label"], "needed_budget_cad": base[r["id"]],
                "budget_increase_pct": round(100 * (base[r["id"]] / budget - 1), 1),
                "cost_cut_pct": round(100 * (1 - budget / base[r["id"]]), 1),
            })  # fmt: skip
        elif rules:
            reasons = [d["message"] for d in details
                       if d["rule"] != "budget"]  # fmt: skip
            blocked.append({"id": r["id"], "label": r["label"], "reason": "; ".join(reasons)})
    switch_points.sort(key=lambda s: s["needed_budget_cad"])

    economics_check = None
    hours = rec["comparison"]["vehicle_hours_saved"]
    if headroom and hours > 0:
        yearly_hours = hours * scenario.occupancy * scenario.operating_days

        def annualized(cost_factor):
            return (
                base[recommended_id] * cost_factor / scenario.asset_life_years
                + scenario.annual_operating_cost_cad
            )

        def net(cost_factor, vot_factor):
            return yearly_hours * scenario.value_of_time_cad * vot_factor - annualized(cost_factor)

        economics_check = {
            "net_annual_value_cad": round(net(1, 1), 2),
            "worst_case_net_cad": round(net(1.5, 0.5), 2),
            "worst_case": "costs +50% and value of time -50%",
            "break_even_value_of_time_cad": round(annualized(1) / yearly_hours, 2),
            "value_of_time_cad": scenario.value_of_time_cad,
        }

    if robust == len(cells):
        verdict = (
            f"Robust: {label} stays the recommendation for every tested combination of "
            "costs and budget (each -50% to +50%)."
        )
    else:
        parts = []
        if headroom:
            parts.append(
                f"its cost rises more than {headroom['cost_increase_pct']:g}% "
                f"(above ${budget:,.0f}), when {headroom['fallback']} takes over"
            )
        if switch_points:
            s = switch_points[0]
            parts.append(
                f"the budget reaches ${s['needed_budget_cad']:,.0f} "
                f"(+{s['budget_increase_pct']:g}%), when {s['label']} becomes affordable"
            )
        verdict = f"{label} wins in {robust} of {len(cells)} cost/budget combinations."
        if parts:
            verdict += " It changes if " + " or if ".join(parts) + "."
    return {
        "recommended_id": recommended_id,
        "cost_factors": list(COST_FACTORS),
        "budget_factors": list(BUDGET_FACTORS),
        "grid": grid,
        "robust_share_pct": round(100 * robust / len(cells), 1),
        "verdict": verdict,
        "headroom": headroom,
        "switch_points": switch_points,
        "blocked": blocked,
        "one_at_a_time": one_at_a_time,
        "economics": economics_check,
        "method": "Re-applies the study rule (lowest modeled delay among options that pass "
        "budget, cross-street and complete-trip checks) with every capital cost and the budget "
        "scaled from -50% to +50%; simulated delays are unchanged because costs do not affect "
        "traffic. One-at-a-time rows scale a single option's cost.",
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
