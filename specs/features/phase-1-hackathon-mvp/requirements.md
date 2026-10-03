# S-BB-1 — Bottleneck lab requirements

Implementation contract settled October 3 under user's early-build authorization.
External organizer acceptance open. [US-BB-001](../../../docs/user_stories/planning.md),
[UJ-BB-001](../../../docs/user_journeys/planner.md),
[UJ-BB-002](../../../docs/user_journeys/budget_reviewer.md),
[DES-BB-001](../../../docs/design/bottleneck-lab/design.md).

Client/problem grounding: [research index](../../../docs/product_research/README.md).
Customer journey and productivity claims remain hypotheses. Current application
compares a specified synthetic corridor; it does not rank City bottlenecks or
prioritize asset maintenance funding. Research adds no new runtime scope.

FR-1 Attributed Calgary incident snapshot and reproducible refresh, separate from flow.
FR-2 Real SUMO execution on explicit synthetic corridor/demand; normalized measured
profile import with validated units and provenance; no claimed calibration.
FR-3 Equal-green reference, demand-based candidate, outcome-based revision,
capacity alternative; equivalent inputs/seed/horizon; numerical outputs from engine.
FR-4 Budget and cross-street delay guardrail; feasible reference fallback;
Pareto cost-delay frontier, rejection reasons.
FR-5 Chronological agent/tool trace; disjoint hold-out seeds and ±20% flow stress.
FR-6 Account for completed/unfinished/uninserted trips, departure waiting,
traffic delay/queues; no teleport or hidden simulator failure.
FR-7 Separate frontend shows controls, job progress, trace, modeled network activity,
actual alternatives, economics/Pareto and downloadable evidence.
FR-8 Editable estimated costs, occupancy, value of time, operating days; no City quotes.
TR-1 Pure domain/application/infra/API; separate frontend; pinned dependency locks.
TR-2 Bounded jobs/strict input validation/fixed subprocess/temp paths; local-only.
TR-3 Contribution ownership, launch/test commands, meaningful tests and demo guide.

## Acceptance

AC-1 Sources/modeling links resolve; four spec files; organizer originals preserved.
AC-2 Refresh succeeds or explicit failure; offline snapshot usable with provenance.
AC-3 Actual baseline/candidate/revision/capacity runs, deterministic demand,
hold-out separated from tuning; all demand accounted.
AC-4 Budget/guardrail and fallback tested; failures explicit; economics units checked.
AC-5 UI triggers actual backend job/result/export; production build and domain/API/
real-simulation tests pass locally.
AC-6 Contribution guide, five-minute demo and approval draft exist. External acceptance,
measured flow/calibration, deployment and final submission remain separate open gates.

Out of scope: citywide twin, real signal control/removal, RL training, crash-risk proof.

FR-9 User-requested guided flow: problem, interventions/constraints, actual simulation,
recommendation. Evidence remains separately accessible; edited inputs clearly mark
prior results stale. Mobile navigation has accessible names; no page-wide overflow.
