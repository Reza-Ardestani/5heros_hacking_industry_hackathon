# US-BB-001 — Budget-aware bottleneck planning

Journey: [UJ-BB-001](../user_journeys/planner.md).

- BB-1 Planner inspects source versions and assumptions. Acceptance: public
  incident provenance and synthetic demand/network/cost labels visible.
- BB-2 Engineer compares identical departures across alternatives. Acceptance:
  input hash/seed/horizon/version, completed/unfinished/uninserted trips and no
  silent teleport; true simulation results, not invented improvements.
- BB-3 Planner sets budget/cross-street guardrail. Acceptance: ineligible changes
  excluded with reasons; no-change reference remains feasible fallback.
- BB-4 Engineer sees autonomous revision. Acceptance: chronological trace includes
  actual tool outcomes, changed parameters, rationale and final evaluation.
- BB-5 Budget reviewer exports cost-delay evidence. Acceptance: Pareto options,
  user-editable economics, complete assumptions/limitations in JSON report.
- BB-6 Teammate reproduces/extends prototype. Acceptance: frontend/backend separate,
  dependency locks, focused tests and contribution boundaries.
