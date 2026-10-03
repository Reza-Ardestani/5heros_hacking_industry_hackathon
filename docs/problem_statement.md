# Which Calgary bottlenecks keep us stuck?

For a specified corridor, which permitted intervention should an engineer take
forward for review, given cost and service constraints? Bottleneck Busters tests
an auditable comparison/revision workflow for that decision. It does not yet
rank Calgary corridors or prove that a road intervention works in the field.

Incidents identify reported disruptions, not traffic demand, measured congestion
or exposure-adjusted risk. A defensible comparison needs counts, a network/signal
model, constraints and validation. The current executable experiment uses an
explicitly synthetic corridor and equal-green reference.

## Current workflow and pains — hypotheses

Calgary has an operational signal system and formal asset planning; optimization
and simulation products already exist. [Research ledger](product_research/evidence.md).
No direct practitioner interview has been established; the earlier anecdote is
not evidence of absent tools, staffing gaps or random decisions.

Working journey hypothesis: an engineer establishes the study scope, assembles
counts/geometry/timings, validates a baseline, compares alternatives and prepares
a recommendation. Test whether repeated reruns, constraint checks and reviewer
handoffs are costly despite existing tools. Our current slice automates its fixed
scenario's comparison/revision/reporting, not preparation of a measured model.
We have not established that current solutions are insufficient.

## User and MVP

Primary candidate: municipal transportation engineer or consultant study lead;
secondary: mobility program/budget reviewer. [ICP](product_research/ideal_client_profile.md),
[engineer journey](user_journeys/planner.md), [reviewer journey](user_journeys/budget_reviewer.md).
One bounded study: inspect provenance, set budget/service guardrail, compare
retiming/capacity changes, revise from simulation outcomes, present cost-delay
options and export evidence. Human engineering review precedes real implementation.
Maintenance/renewal portfolio prioritization is a separate decision; asset
condition, failure risk and lifecycle planning are absent from this application.

## Algorithm and feature engineering

Weekend: simulation-based bounded search. No trained ML/RL: calibrated training
environment, reward design and independent evaluation are absent. Extra AI credits
do not supply ground truth. Later: surrogate regression/Bayesian optimization;
RL only after valid training/evaluation environment.

Features: directional arrivals per interval, turning proportions, heavy-vehicle
share; lane counts, allowed movements, speed, signal phases; incident direction,
lane impact, location/time and extraction confidence. Weekday/weather features
only if measured. Incident frequency never substitutes for flow or delay.

## Objective, cost and uncertainty

Minimize total modeled vehicle delay subject to budget and cross-street delay
increase guardrail. Report cost/delay Pareto frontier. Optional economics:
passenger-hours saved × assumed CAD/person-hour × modeled operating days,
minus annualized capital and annual operations costs. Occupancy, value of time,
asset life, operating days and costs are editable assumptions, not City quotes.
Do not extrapolate one scenario to all Calgary. Safety, induced demand,
pedestrians, land availability and construction impacts need engineering review.

## Pilot/commercialization hypothesis

Use the [discovery plan](product_research/discovery_plan.md) to validate one
recurring workflow gap. Reproduce a consultant/City corridor study before
proposing changes; validate against observations. Compare time to a correct
reviewable deliverable with the customer's existing process, including setup and
engineering corrections. Customer, willingness to pay, productivity savings,
procurement and field effects remain unverified. [Judge brief](demo/judge_brief.md).
