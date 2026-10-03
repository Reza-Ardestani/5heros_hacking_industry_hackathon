"""A bounded tool-using plan/score/revise loop with independently scored trials."""

from dataclasses import asdict
from datetime import UTC, datetime

from app.domain.evaluation import aggregate, compare, economics, pareto
from app.domain.models import Intervention, Scenario, bounded_share


class PlanningService:
    def __init__(self, simulator):
        self.simulator = simulator

    def run(self, scenario: Scenario, emit) -> dict:
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
        event(
            "Data auditor",
            "inspect",
            "Demand and network provenance checked; costs are estimates.",
            demand_kind=scenario.demand_kind,
            demand_source=scenario.demand_source,
            network_kind="synthetic three-intersection corridor",
            main_vph=main,
            cross_vph=cross,
        )
        version = self.simulator.version()
        reference = Intervention("reference", "Equal-green reference", 0.5, 1, 0)
        initial = Intervention(
            "candidate",
            "Demand-based retiming",
            bounded_share(main / (main + cross)),
            1,
            scenario.retiming_cost_cad,
        )
        event("Simulation agent", "run_reference", "Run unchanged equal-green baseline.")
        base_trial = self.simulator.run(scenario, reference, scenario.seed, playback=True)
        event(
            "Simulation agent",
            "reference_scored",
            "Actual SUMO reference completed.",
            metrics=base_trial["metrics"],
            demand_sha256=base_trial["demand_sha256"],
        )
        event(
            "Planning agent",
            "propose",
            "Allocate green to observed arrival imbalance; keep clearance/service bounds.",
            proposal=asdict(initial),
        )
        initial_trial = self.simulator.run(scenario, initial, scenario.seed, playback=True)
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
            "revised", "Outcome-based revision", bounded_share(share), 1, scenario.retiming_cost_cad
        )
        event("Revision agent", "revise", rationale, proposal=asdict(revised))
        revised_trial = self.simulator.run(scenario, revised, scenario.seed, playback=True)
        widening = Intervention(
            "capacity",
            "Add arterial lane (capacity experiment)",
            0.5,
            2,
            scenario.widening_cost_cad,
        )
        event(
            "Planning agent",
            "capacity_alternative",
            "Compare lane capacity as separately costed, unverified construction option.",
            proposal=asdict(widening),
        )
        capacity_trial = self.simulator.run(scenario, widening, scenario.seed, playback=True)
        interventions = [reference, initial, revised, widening]
        tuning_trials = [base_trial, initial_trial, revised_trial, capacity_trial]
        # Freeze all proposals before touching these hold-out seeds.
        seeds = [scenario.seed + 101, scenario.seed + 202, scenario.seed + 303]
        rows = []
        for intervention, tuning in zip(interventions, tuning_trials):
            event(
                "Evaluation agent",
                "holdout",
                f"Evaluate frozen {intervention.label} on three unseen seeds.",
            )
            trials = [self.simulator.run(scenario, intervention, seed) for seed in seeds]
            row = {
                **asdict(intervention),
                "metrics": aggregate([t["metrics"] for t in trials]),
                "holdout_trials": trials,
                "tuning_trial": tuning,
            }
            rows.append(row)
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
            stress_reference = self.simulator.run(scenario, reference, scenario.seed + 404, factor)
            stress_selected = self.simulator.run(scenario, selected, scenario.seed + 404, factor)
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
        event(
            "Reporting agent",
            "recommend",
            f"Select {best['label']} by constrained hold-out total delay.",
            selected_id=best["id"],
            frontier=frontier,
            stress_passed=stress_passed,
        )
        return {
            "scenario": scenario.model_dump(),
            "simulator_version": version,
            "reference_definition": "Synthetic equal-green signal plan; not Calgary's observed timings",
            "network_kind": "Synthetic straight-through three-intersection corridor",
            "evaluation": {
                "optimization_seed": scenario.seed,
                "holdout_seeds": seeds,
                "stress_seed": scenario.seed + 404,
                "paired_departures": True,
                "objective": "Minimize total SUMO timeLoss + departure delay within budget/guardrail",
            },
            "alternatives": rows,
            "pareto_ids": frontier,
            "recommended_id": best["id"],
            "stress_tests": stress,
            "stress_passed": stress_passed,
            "claim": "Modeled comparative evidence; no calibrated Calgary field-effect claim",
            "limitations": [
                "Synthetic corridor geometry and default demand; no observed signal timings",
                "Imported measured arrivals alone do not calibrate travel times or routing",
                "Only straight trips; pedestrian, turn, bus and induced-demand effects omitted",
                "Costs, occupancy and annual operating assumptions are illustrative",
                "Three hold-out seeds are preliminary evidence, not broad statistical validation",
                "Stress failures block a robust pilot claim; inspect individual trials",
                "No construction feasibility, safety assessment or real signal control",
            ],
        }
