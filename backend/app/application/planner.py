"""A bounded tool-using plan/score/revise loop with independently scored trials.

Default inputs reproduce the original four options (reference, demand-based retiming,
outcome-based revision, extra lane). Optional study features add options at the hotspot
junction (J2): signal vs priority control, faster incident clearance, left-turn bay with
a protected phase, and a left-turn ban. With an incident and incident_weight < 1, every
option is evaluated in normal and incident conditions and the two are weighted by how
often an incident is active (from City data for intersection studies).
"""

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import UTC, datetime

from app.domain.evaluation import (
    aggregate,
    compare,
    cost_stress,
    economics,
    explain_decision,
    pareto,
)
from app.domain.models import Intervention, Scenario, bounded_share

HOLDOUT_WORKERS = max(1, min(4, (os.cpu_count() or 2) - 1))


def mix(normal: dict, incident: dict, weight: float) -> dict:
    return {k: (1 - weight) * normal[k] + weight * incident[k] for k in normal}


class PlanningService:
    def __init__(self, simulator):
        self.simulator = simulator

    def run(self, scenario: Scenario, emit, context=None) -> dict:
        def event(agent, action, detail, **evidence):
            emit(
                {
                    "at_utc": datetime.now(UTC).isoformat(),
                    "agent": agent,
                    "action": action,
                    "detail": detail,
                    **evidence,
                }
            )

        main, cross = scenario.average_flows()
        lanes = scenario.arterial_lanes
        incident = scenario.incident
        weight = scenario.incident_weight if incident else 0.0
        normal = scenario.model_copy(update={"incident": None})
        # Tuning, playback and stress use the dominant condition.
        tuning_scenario = scenario if weight >= 0.5 else normal
        event(
            "Data auditor",
            "inspect",
            "Demand and network provenance checked; costs are estimates.",
            demand_kind=scenario.demand_kind,
            demand_source=scenario.demand_source,
            network_kind="synthetic three-intersection corridor",
            main_vph=main,
            cross_vph=cross,
            arterial_lanes=lanes,
            hotspot_control=scenario.junction_control,
            turn_share=scenario.turn_share,
            incident=incident.model_dump() if incident else None,
            incident_weight=weight,
        )
        if incident:
            event(
                "Data auditor",
                "incident_conditions",
                (
                    f"Evaluate options in normal conditions and with a {incident.duration_s // 60}-min "
                    f"{incident.lanes_blocked}-lane {incident.direction}bound incident at J2, weighted "
                    f"{weight:.1%} incident / {1 - weight:.1%} normal."
                ),
            )
        version = self.simulator.version()
        reference = Intervention(
            "reference",
            "Equal-green reference" if scenario.junction_control == "signal"
            else "Current priority control at J2",
            0.5, lanes, 0, kind="reference",
        )  # fmt: skip
        initial = Intervention(
            "candidate",
            "Demand-based retiming",
            bounded_share(main / (main + cross)),
            lanes,
            scenario.retiming_cost_cad,
        )
        event("Simulation agent", "run_reference", "Run unchanged reference plan.")
        base_trial = self.simulator.run(tuning_scenario, reference, scenario.seed, playback=True)
        event(
            "Simulation agent",
            "reference_scored",
            "Actual SUMO reference completed.",
            metrics=base_trial["metrics"],
            demand_sha256=base_trial["demand_sha256"],
        )
        incident_impact = None
        if incident:
            with_incident = (
                base_trial
                if tuning_scenario is scenario
                else self.simulator.run(scenario, reference, scenario.seed)
            )
            without = (
                base_trial
                if tuning_scenario is normal
                else self.simulator.run(normal, reference, scenario.seed)
            )
            extra = with_incident["metrics"]["total_delay_s"] - without["metrics"]["total_delay_s"]
            planned = max(1, without["metrics"]["planned"])
            incident_impact = {
                "extra_delay_s_per_vehicle": extra / planned,
                "vehicle_hours_lost": extra / 3600,
                "with_incident_mean_delay_s": with_incident["metrics"]["mean_delay_s"],
                "normal_mean_delay_s": without["metrics"]["mean_delay_s"],
            }
            event(
                "Simulation agent",
                "measure_incident",
                (
                    f"Reference with vs without the incident: +{extra / planned:.1f} s per vehicle "
                    f"({extra / 3600:.1f} vehicle-hours) on the proposal seed."
                ),
                incident_impact=incident_impact,
            )
        event(
            "Planning agent",
            "propose",
            "Allocate green to observed arrival imbalance; keep clearance/service bounds.",
            proposal=asdict(initial),
        )
        initial_trial = self.simulator.run(tuning_scenario, initial, scenario.seed, playback=True)
        base_row = {**asdict(reference), "metrics": base_trial["metrics"]}
        first_row = {**asdict(initial), "metrics": initial_trial["metrics"]}
        comparison = compare(first_row, base_row, scenario.budget_cad, scenario.cross_guardrail_pct)
        event(
            "Evaluation agent",
            "candidate_scored",
            "Read actual delay and budget/cross-street constraints.",
            metrics=initial_trial["metrics"],
            comparison=comparison,
        )
        if comparison["cross_delay_change_pct"] > scenario.cross_guardrail_pct:
            fraction = min(
                0.75,
                scenario.cross_guardrail_pct / max(1, comparison["cross_delay_change_pct"]) * 0.8,
            )
            share = 0.5 + (initial.main_green_share - 0.5) * fraction
            rationale = "Cross-street guardrail exceeded; scale green change by allowed/observed delay increase with 20% margin."
        elif (
            initial_trial["metrics"]["main_mean_delay_s"]
            > initial_trial["metrics"]["cross_mean_delay_s"]
        ):
            share = initial.main_green_share + 0.05
            rationale = "Main-axis delay remains larger; add bounded main green and rescore."
        else:
            share = initial.main_green_share - 0.05
            rationale = "Cross-axis delay larger; restore cross-street green and rescore."
        revised = Intervention(
            "revised",
            "Outcome-based revision",
            bounded_share(share),
            lanes,
            scenario.retiming_cost_cad,
        )
        event("Revision agent", "revise", rationale, proposal=asdict(revised))
        revised_trial = self.simulator.run(tuning_scenario, revised, scenario.seed, playback=True)
        widening = Intervention(
            "capacity",
            "Add arterial lane (capacity experiment)",
            0.5,
            min(4, lanes + 1),
            scenario.widening_cost_cad,
            kind="capacity",
        )
        event(
            "Planning agent",
            "capacity_alternative",
            "Compare lane capacity as separately costed, unverified construction option.",
            proposal=asdict(widening),
        )
        capacity_trial = self.simulator.run(tuning_scenario, widening, scenario.seed, playback=True)
        interventions = [reference, initial, revised, widening]
        tuning_trials = [base_trial, initial_trial, revised_trial, capacity_trial]

        for option in self._extra_options(scenario, lanes):
            intervention, rationale = option
            event(
                "Planning agent",
                f"propose_{intervention.kind}",
                rationale,
                proposal=asdict(intervention),
            )
            trial = self.simulator.run(tuning_scenario, intervention, scenario.seed, playback=True)
            event(
                "Simulation agent",
                f"{intervention.kind}_scored",
                (
                    f"{intervention.label}: {trial['metrics']['mean_delay_s']:.1f} s/vehicle on the "
                    "proposal seed (reference "
                    f"{base_trial['metrics']['mean_delay_s']:.1f} s)."
                ),
                metrics=trial["metrics"],
            )
            interventions.append(intervention)
            tuning_trials.append(trial)

        # Freeze all proposals before touching these hold-out seeds.
        seeds = [scenario.seed + 101, scenario.seed + 202, scenario.seed + 303]
        conditions = (
            [("normal", normal, 1 - weight), ("incident", scenario, weight)]
            if incident and 0 < weight < 1
            else [("incident" if incident else "normal", scenario, 1.0)]
        )
        # Hold-out trials are independent SUMO processes: run them concurrently. Each
        # result is keyed by (option, condition, seed), so ordering cannot change outcomes.
        tasks = [
            (i, name, condition_scenario, seed)
            for i in range(len(interventions))
            for name, condition_scenario, _ in conditions
            for seed in seeds
        ]
        for intervention in interventions:
            event(
                "Evaluation agent",
                "holdout",
                f"Evaluate frozen {intervention.label} on three unseen seeds"
                + (" in normal and incident conditions." if len(conditions) > 1 else "."),
            )
        with ThreadPoolExecutor(max_workers=HOLDOUT_WORKERS) as pool:
            outcomes = list(
                pool.map(lambda t: self.simulator.run(t[2], interventions[t[0]], t[3]), tasks)
            )
        holdout = {(t[0], t[1], t[3]): o for t, o in zip(tasks, outcomes, strict=True)}
        rows = []
        for i, (intervention, tuning) in enumerate(zip(interventions, tuning_trials, strict=True)):
            trials, by_condition = [], {}
            for name, _, _ in conditions:
                runs = [holdout[(i, name, seed)] for seed in seeds]
                for t in runs:
                    t["condition"] = name
                trials += runs
                by_condition[name] = aggregate([t["metrics"] for t in runs])
            metrics = (
                mix(by_condition["normal"], by_condition["incident"], weight)
                if len(conditions) > 1
                else next(iter(by_condition.values()))
            )
            rows.append(
                {
                    **asdict(intervention),
                    "metrics": metrics,
                    "metrics_by_condition": by_condition,
                    "holdout_trials": trials,
                    "tuning_trial": tuning,
                }
            )
        for row in rows:
            row["comparison"] = compare(
                row, rows[0], scenario.budget_cad, scenario.cross_guardrail_pct
            )
            row["economics"] = economics(
                row["comparison"]["vehicle_hours_saved"], row["capital_cost_cad"], scenario
            )
        frontier = pareto(rows)
        eligible = [r for r in rows if r["comparison"]["feasible"]]
        best = (
            min(eligible, key=lambda r: (r["metrics"]["total_delay_s"], r["capital_cost_cad"]))
            if eligible
            else rows[0]
        )
        selected = next(i for i in interventions if i.id == best["id"])
        stress = []
        for factor in (0.8, 1.2):
            event(
                "Evaluation agent",
                "stress_test",
                f"Check selected plan at {factor:.0%} arrival demand.",
            )
            stress_reference = self.simulator.run(
                tuning_scenario, reference, scenario.seed + 404, factor
            )
            stress_selected = self.simulator.run(
                tuning_scenario, selected, scenario.seed + 404, factor
            )
            stress.append(
                {
                    "demand_factor": factor,
                    "reference": stress_reference,
                    "selected": stress_selected,
                    "comparison": compare(
                        {**asdict(selected), "metrics": stress_selected["metrics"]},
                        {**asdict(reference), "metrics": stress_reference["metrics"]},
                        scenario.budget_cad,
                        scenario.cross_guardrail_pct,
                    ),
                }
            )
        stress_passed = all(
            s["comparison"]["feasible"] and s["comparison"]["delay_reduction_pct"] >= 0
            for s in stress
        )
        decision = explain_decision(rows, best["id"])
        lowest_label = next(r["label"] for r in rows if r["id"] == decision["lowest_delay_id"])
        why = (
            f"Select {best['label']} by constrained hold-out total delay."
            if decision["lowest_delay_is_recommended"]
            else f"Select {best['label']}; lowest-delay option {lowest_label} is rejected: "
            f"{'; '.join(decision['lowest_delay_rejected_because'])}."
        )
        event(
            "Reporting agent",
            "recommend",
            why,
            selected_id=best["id"],
            lowest_delay_id=decision["lowest_delay_id"],
            frontier=frontier,
            stress_passed=stress_passed,
        )
        limitations = [
            "Synthetic corridor geometry and default demand; no observed signal timings",
            "Imported measured arrivals alone do not calibrate travel times or routing",
            "Pedestrian, bus and induced-demand effects omitted",
            "Costs, occupancy and annual operating assumptions are illustrative",
            "Three hold-out seeds are preliminary evidence, not broad statistical validation",
            "Stress failures block a robust pilot claim; inspect individual trials",
            "No construction feasibility, safety assessment or real signal control",
        ]
        if scenario.turn_share:
            limitations.append(
                "Left-turn share is an assumption (no turning counts); a turn ban adds a fixed "
                "36 s backtrack penalty per diverted vehicle"
            )
        if incident:
            limitations.append(
                "Incidents are modeled as stopped vehicles blocking lanes at J2; duration and "
                "frequency weighting come from assumptions and City incident records, not "
                "measured clearance times"
            )
        if "signal_control" in scenario.extra_options:
            limitations.append(
                "Signal/priority comparisons cover delay only; collision and pedestrian safety "
                "effects of adding or removing a signal are not modeled"
            )
        return {
            "scenario": scenario.model_dump(),
            "simulator_version": version,
            "reference_definition": reference.label + "; synthetic, not Calgary's observed timings",
            "network_kind": "Synthetic straight-through three-intersection corridor"
            + (" with left turns at J2" if scenario.turn_share else ""),
            "evaluation": {
                "optimization_seed": scenario.seed,
                "holdout_seeds": seeds,
                "stress_seed": scenario.seed + 404,
                "paired_departures": True,
                "conditions": [{"name": n, "weight": w} for n, _, w in conditions],
                "objective": "Minimize total SUMO timeLoss + departure delay within budget/guardrail",
            },
            "alternatives": rows,
            "pareto_ids": frontier,
            "recommended_id": best["id"],
            "decision": decision,
            "incident_impact": incident_impact,
            "stress_tests": stress,
            "stress_passed": stress_passed,
            "cost_stress": cost_stress(rows, best["id"], scenario),
            "claim": "Modeled comparative evidence; no calibrated Calgary field-effect claim",
            "limitations": limitations,
        }

    @staticmethod
    def _extra_options(scenario: Scenario, lanes: int):
        opts = set(scenario.extra_options)
        if "signal_control" in opts:
            if scenario.junction_control == "signal":
                yield (
                    Intervention(
                        "signal_control", "Remove signal at J2 (priority control)", 0.5, lanes,
                        scenario.signal_removal_cost_cad, control="priority", kind="signal",
                    ),
                    (
                        "Test replacing the J2 signal with priority control (arterial keeps right "
                        "of way, cross street yields). Delay only; safety needs separate review."
                    ),
                )  # fmt: skip
            else:
                yield (
                    Intervention(
                        "signal_control", "Add signal at J2", 0.5, lanes,
                        scenario.signal_install_cost_cad, control="signal", kind="signal",
                    ),
                    "Test installing an equal-green signal at the currently unsignalized J2.",
                )  # fmt: skip
        if "incident_clearance" in opts and scenario.incident:
            cut = scenario.clearance_reduction
            yield (
                Intervention(
                    "incident_clearance", f"Faster incident clearance (-{cut:.0%} duration)", 0.5,
                    lanes, scenario.clearance_program_cost_cad,
                    incident_duration_factor=round(1 - cut, 3), kind="clearance",
                ),
                f"Test a response program that clears lane-blocking incidents {cut:.0%} sooner.",
            )  # fmt: skip
        if "turn_lane" in opts and scenario.turn_share:
            yield (
                Intervention(
                    "turn_lane", "Left-turn bay + protected phase at J2", 0.5, lanes,
                    scenario.turn_lane_cost_cad, turn_lane=True, kind="turn_lane",
                ),
                (
                    "Separate left turners into a bay with a 10 s protected phase so they stop "
                    "blocking through traffic."
                ),
            )  # fmt: skip
        if "turn_ban" in opts and scenario.turn_share:
            yield (
                Intervention(
                    "turn_ban", "Ban left turns at J2 (use next junction)", 0.5, lanes,
                    scenario.turn_ban_cost_cad, turn_ban=True, kind="turn_ban",
                ),
                "Remove left turns at J2; turners continue to the next junction and backtrack.",
            )  # fmt: skip
