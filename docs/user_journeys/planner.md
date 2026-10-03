# UJ-BB-001 — Engineer compares corridor interventions

Canonical local journey for this separate hackathon product; [catalog](../modeling.md).
Updated October 3, 2026. As-is steps are a research-informed hypothesis, not an
observed Calgary workflow. [Research](../product_research/evidence.md),
[candidate client](../product_research/ideal_client_profile.md).

## Actor, trigger and outcome

Actor: municipal transportation engineer or consultant study lead. Trigger:
a request to compare retiming with added capacity on an already specified
corridor before review. Success: a reproducible shortlist whose constraints,
assumptions and rejection reasons another professional can inspect.

This journey begins with a chosen study; citywide bottleneck identification is
not implemented. The current walkthrough demonstrates the study on a synthetic
model. A calibrated professional use case requires additional input/model work.

## As-is and proposed journey

| Stage | Current workflow hypothesis | Pain to validate | Proposed application experience | Current boundary |
|---|---|---|---|---|
| Frame | Agree corridor, decision, time period and objectives with study sponsor | Ambiguous decision or conflicting expectations | Problem step explains the experiment; engineer sets demand and constraints | Fixed three-junction geometry; no real corridor selection |
| Establish evidence | Obtain appropriate counts, geometry, timings and observations; validate baseline | Data transformation and review effort | Evidence view exposes provenance; optional sourced directional-profile import | No complete CalTRACS adapter, observed geometry/timings or baseline calibration |
| Define options | Choose feasible alternatives and obtain scoped cost estimates | Assumptions scattered across model/report | Interventions step edits capital budget, cost assumptions and cross guardrail | Two action types; estimated costs, no construction feasibility |
| Compare | Run model alternatives on an agreed analysis protocol | Repeated runs and constraint checks | Simulation step executes four alternatives on paired demands and frozen evaluation seeds | Native SUMO on synthetic model; three seeds are preliminary |
| Revise | Inspect weak alternatives, change parameters and rerun | Manual iteration and lost rationale | Policy reads actual delay, revises green split, logs rationale and outcomes | Bounded deterministic policy; no generalized autonomous engineering |
| Recommend | Assemble results, explain exclusions and hand over evidence | Reviewer questions require reconstructing analysis | Recommendation step shows cost-delay options, rejection reasons, stress checks and JSON export | Modeled effect only; aggregates omit turns, transit and pedestrians |
| Review/pilot | Technical review, decision authorization, further evidence and any field test | Trust and accountability | Export supports an external reviewer conversation | Engineering approval and field deployment are outside the app |

Research supports existence of tools/data and review methodology. It does not
establish the hypothesized pains, their frequency, or the local order of steps.

## Demonstrable path today

Follow Problem, Interventions, Simulation, Recommendation. With default inputs,
observe the first retiming fail its cross-street guardrail, the revision pass,
and the capacity option exceed assumed budget. Inspect actual results, source
labels and the exported report; never interpret the equal-green reference as
Calgary's present signal plan. [Implemented stories](../user_stories/planning.md).

## Recovery and handoff

Invalid inputs block the job; a busy worker reports a conflict. Engine failure is
explicit. A feasible reference can remain selected when paid choices are
ineligible. Incomplete trips make comparisons ineligible. Stress failure prevents
a robust-pilot claim, but is not a hard recommendation filter in current code.
Edited inputs mark prior results stale and require a new run. Imported source
declarations do not certify measured data. API restart loses local job history.

The [budget reviewer journey](budget_reviewer.md) starts at the recommendation/
report handoff. No in-app sign-off or municipal approval workflow exists.
[Study handoff diagram](../diagrams/study_journey.md).
