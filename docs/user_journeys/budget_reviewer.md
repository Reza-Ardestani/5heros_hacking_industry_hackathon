# UJ-BB-002 — Program reviewer inspects an intervention shortlist

Canonical local journey; [catalog](../modeling.md). Proposed workflow, October 3,
2026. No budget reviewer has been interviewed; titles, authority and required
deliverables remain hypotheses. [ICP](../product_research/ideal_client_profile.md).

Actor: mobility program manager or budget analyst receiving an engineer's study.
Trigger: review whether a corridor option merits further engineering/pilot work
within a stated budget. Outcome: an informed next-step decision or a request for
missing evidence, not automatic project approval.

| Stage | Current workflow hypothesis | Proposed experience | Implemented support and limit |
|---|---|---|---|
| Understand decision | Read study summary; ask what corridor/period/baseline it concerns | Inspect scenario and named reference | Current reference is synthetic; no observed corridor reproduced |
| Check evidence | Ask for sources, counts, model validity and cost scope | Inspect inputs, provenance and limitations alongside result | Labels and source context exported; source/calibration not independently certified |
| Compare tradeoffs | Reconcile performance tables with costs and service priorities | Inspect four options, feasibility, Pareto cost-delay view | Capital and cross-mean-delay checks only; other policy objectives absent |
| Challenge recommendation | Ask why the first proposal or construction option was rejected | Inspect agent trace and rejection reasons; rerun edited assumptions with engineer | Actual trace and rerun work locally; no collaborative review or approval state |
| Assess uncertainty | Request sensitivity tests and evidence of model validity | Read per-seed completion and ±20% demand checks | Preliminary model checks; not calibrated effects or a confidence interval |
| Decide next step | Request more study, pursue an approved pilot, or decline | Export evidence for the existing review process | JSON handoff available; decision, funding and signal operation stay external |

Proposed pains: reconstructing assumptions, reconciling cost/performance figures,
and explaining exclusions. These require discovery; none is claimed as a proven
City problem. A reviewer may find existing deliverables sufficient.

Missing geometry/timings/calibration, invalid cost scope, omitted modes, censored
trips, or stress failure should prompt further engineering evidence. Current
prototype cannot approve even a constraint-compliant alternative for field use.

Related [engineer journey](planner.md), [stories BB-1/3/4/5](../user_stories/planning.md),
[study handoff diagram](../diagrams/study_journey.md),
[interview/pilot plan](../product_research/discovery_plan.md).
