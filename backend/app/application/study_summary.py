"""Evidence summary for a study: six months of City data + modeled option effects.

Deterministic text built from numbers (no language model). Every statement says whether
it is observed (City records) or modeled (SUMO on the synthetic corridor).
"""

from app.domain.models import Scenario

KIND_EXPLANATION = {
    "retiming": "Signal retiming at all three junctions",
    "capacity": "An extra arterial lane in each direction",
    "signal": "Changing traffic control at the hotspot junction",
    "clearance": "Clearing lane-blocking incidents faster",
    "turn_lane": "A dedicated left-turn bay with a protected phase",
    "turn_ban": "Banning left turns at the hotspot junction",
}
PROOF_STANDARD = (
    "City records show where and how often disruptions occur; they do not measure delay. "
    "Improvements are modeled on a synthetic corridor using those records (demand from 2024 "
    "volumes, incident frequency/lanes). Field effect needs calibrated counts and "
    "engineering review."
)


def _pct(x):
    return f"{x:+.1f}%"


def _observed_facts(context, scenario, impact):
    facts = []
    if context:
        e = context["evidence"]
        key = context["intersection_key"]
        facts.append(
            f"{e['incidents']} City-reported incidents at {key} over {e['observed_days']} days "
            f"({e['per_month']:.1f} per month)."
        )
        facts.append(
            f"{e['lane_blocking']} ({e['lane_blocking_pct']:.0f}%) blocked at least one lane; "
            f"{e['peak_lane_blocking']} of those started in a weekday peak period."
        )
        facts.append(
            f"{e['unspecified']} ({e['unspecified_pct']:.0f}%) are 'Traffic incident' with no "
            "stated cause."
        )
        facts.append(
            f"{e['collisions']} collisions, {e['vulnerable_road_user']} involving a pedestrian "
            f"or cyclist, {e['signal_faults']} signal faults."
        )
        if e.get("live_now"):
            facts.append(f"Live now: {e['live_now']}.")
        if scenario.incident:
            facts.append(
                f"Incident weighting used in the comparison: {scenario.incident_weight:.1%} of "
                "peak windows (lane-blocking peak incidents / observed weekday peak periods)."
            )
        else:
            facts.append("No incident conditions included in this study.")
    if impact:
        facts.append(
            f"Modeled cost of one {scenario.incident.duration_s // 60}-min incident: "
            f"+{impact['extra_delay_s_per_vehicle']:.1f} s per vehicle "
            f"({impact['vehicle_hours_lost']:.1f} vehicle-hours in the study window)."
        )
    return facts


def _option_line(r, reference, recommended, context):
    c = r["comparison"]
    kind = r.get("kind", "retiming")
    line = {
        "id": r["id"],
        "label": r["label"],
        "kind": kind,
        "what": r["label"] if kind == "retiming" else KIND_EXPLANATION.get(kind, r["label"]),
        "modeled_delay_change_pct": round(-c["delay_reduction_pct"], 1),
        "modeled_vehicle_hours_saved": round(c["vehicle_hours_saved"], 2),
        "cross_delay_change_pct": round(c["cross_delay_change_pct"], 1),
        "capital_cost_cad": r["capital_cost_cad"],
        "feasible": c["feasible"],
        "rejected_because": [d["message"] for d in c.get("rejection_details", [])],
        "recommended": r["id"] == recommended["id"],
    }
    cond = r.get("metrics_by_condition") or {}
    ref_cond = reference.get("metrics_by_condition") or {}
    if "incident" in cond and "incident" in ref_cond:
        saved = (ref_cond["incident"]["total_delay_s"] - cond["incident"]["total_delay_s"]) / 3600
        line["incident_vehicle_hours_saved"] = round(saved, 2)
        if context and context["evidence"]["peak_lane_blocking"]:
            n = context["evidence"]["peak_lane_blocking"]
            line["six_month_scaled_vehicle_hours"] = round(saved * n, 1)
    if "normal" in cond and "normal" in ref_cond:
        base = ref_cond["normal"]["total_delay_s"]
        line["normal_delay_change_pct"] = round(
            100 * (cond["normal"]["total_delay_s"] - base) / max(1, base), 1
        )
    sentence = (
        f"{line['what']}: modeled delay {_pct(line['modeled_delay_change_pct'])} vs the "
        f"reference, cross streets {_pct(line['cross_delay_change_pct'])}, "
        f"${r['capital_cost_cad']:,.0f} assumed capital."
    )
    if "six_month_scaled_vehicle_hours" in line:
        n = context["evidence"]["peak_lane_blocking"]
        per_event = line["incident_vehicle_hours_saved"]
        verb = "saves" if per_event >= 0 else "adds"
        sentence += (
            f" During incidents it {verb} {abs(per_event):.1f} vehicle-hours per event; at the "
            f"{n} peak lane-blocking incidents seen in six months that is about "
            f"{abs(line['six_month_scaled_vehicle_hours']):.0f} vehicle-hours "
            f"{'saved' if per_event >= 0 else 'added'} (modeled)."
        )
    if line["rejected_because"]:
        sentence += " Not eligible: " + "; ".join(line["rejected_because"]) + "."
    line["sentence"] = sentence
    return line


def build_summary(result: dict, context: dict | None) -> dict:
    scenario = Scenario(**result["scenario"])
    rows = result["alternatives"]
    reference = rows[0]
    recommended = next(r for r in rows if r["id"] == result["recommended_id"])
    decision = result.get("decision") or {}
    options = [_option_line(r, reference, recommended, context) for r in rows[1:]]
    improving = [o for o in options if o["modeled_delay_change_pct"] < 0]
    best_any = min(options, key=lambda o: o["modeled_delay_change_pct"]) if options else None
    if recommended["id"] != "reference":
        change = -recommended["comparison"]["delay_reduction_pct"]
        headline = f"Recommended: {recommended['label']} ({change:+.1f}% modeled delay)."
    else:
        headline = "Keep the reference: no option improved delay within the study rules."
    if best_any and decision and not decision.get("lowest_delay_is_recommended"):
        headline += (
            f" Largest modeled reduction: {best_any['label']} "
            f"({best_any['modeled_delay_change_pct']:+.1f}%), not eligible: "
            + "; ".join(best_any["rejected_because"])
            + "."
        )
    return {
        "headline": headline,
        "intersection_key": context["intersection_key"] if context else None,
        "observed_facts": _observed_facts(context, scenario, result.get("incident_impact")),
        "options": options,
        "options_that_reduce_delay": [o["id"] for o in improving],
        "proof_standard": PROOF_STANDARD,
    }
