# UJ-BB-001 — Intervention and Prediction

Target client: [ICP-BB-001](../Ideal_Client_Profiles/ICP_1_Planning/profile.md).
Primary actor: municipal transportation engineer or consultant study analyst.
Technical approver: qualified engineering lead. Reviewer/buyer hypothesis: mobility
program manager, budget analyst, or consulting principal. Calgary is the research
anchor, not a confirmed customer. [Stories](User_Stories/README.md).

Trigger: a corridor/intersection shows recurring reported disruptions or a planning
review asks which permitted change merits further study under budget and resource
constraints. Outcome: a reproducible recommendation, rejected-option reasons,
evidence gaps, and an engineering review brief. No field improvement or approval implied.

| Stage | Current workflow hypothesis / pain | Product experience | Evidence / implementation boundary |
|---|---|---|---|
| Frame | Select study and gather reports across tools | Define area, horizon, decision, budget and protected movements | Guided study exists; real geometry/flow calibration incomplete |
| Inspect | Counts, incidents, costs and assumptions require reconciliation | Show source dates/units, modeled inputs and missing measurements | Source context and input labels exist; incidents alone do not establish demand |
| Predict | Prioritize further study from history | Inspect expected City-reported incident counts and baseline comparison | Current forecast exists; newer multi-model selection is on another branch; this is not a calibrated travel-time forecast |
| Qualify resources | Quotes/work schedules may be detached from scenarios | UJ-3 supplies dated labor/material/equipment requirements and availability | Proposed; current costs are editable assumptions |
| Compare | Configure alternatives and repeat simulations | Evaluate permitted changes against identical baseline inputs | SUMO comparison and budget/cross-street checks exist; construction resource gating is proposed |
| Revise | Repeat setup after a rejected option | Agent uses tool results to revise, then rerun with frozen inputs | Coded policy revision exists; not every feature is LLM-driven |
| Review | Explain why an apparently better option lost | Display cost-delay tradeoffs, rejection rules and uncertainty | Explainable decisions/export exist; per-mode protection and real cost verification remain open |
| Pilot | Obtain engineering/operational approval | Export brief and request a supervised real-world validation | Human decision; no direct signal actuation, purchasing or construction dispatch |

Resource-aware example, proposed: if an expansion requires labor or equipment not
available in the study work window, mark it resource-infeasible. Retiming remains
eligible only if its own crew/controller access, budget, safety/service constraints,
and authorization can be satisfied. If availability is unknown, show conditional
status; do not treat unknown as either zero supply or proof of feasibility.

Failure paths: invalid inputs block; missing simulator fails explicitly; no feasible
improvement returns a no-change reference; sparse history exposes forecast limits;
stale cost/resource data withholds an unconditional construction recommendation.
Existing results become stale when inputs change; rerun before claiming an update.

Pain/value remain hypotheses until a practitioner validates them. Compare time to
a correct, reviewable study with the user's existing process, including data prep
and engineering corrections. Do not claim their existing tools are absent.

Dependencies: [UJ-2](../User_Journey_2/journey.md) locates and hands off evidence;
[UJ-3](../User_Journey_3/journey.md) supplies qualified evidence and resource constraints.
[MVP spec](../../specs/features/phase-1-hackathon-mvp/requirements.md),
[intersection spec](../../specs/features/phase-3-intersection-studies/requirements.md),
[resource design](../../docs/design/resource-evidence/design.md).
