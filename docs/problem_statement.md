# Which Calgary bottlenecks keep us stuck?

City Mobility planners need reviewable comparisons of feasible road/signal
changes under limited budget. Incidents identify reported disruptions, not
traffic demand, measured congestion or exposure-adjusted risk. A defensible
comparison needs counts, network/signal model, constraints and validation.

## Current workflow and pains — hypotheses

Engineers assemble counts, inspect geometry, configure professional simulators,
compare alternatives and prepare recommendations. CalTRACS confirms counts
support planning. Manual workload, staffing gaps and pain severity have not
been interviewed/measured; do not claim City staff lack expertise. Existing
simulation tools already support scenario analysis. Proposed value: automated
preparation, constrained revision and evidence packaging.

## User and MVP

Primary: City transportation engineer/planner; secondary: capital budget reviewer.
Province is a later pilot for provincially owned roads. One bounded study area:
inspect data quality, propose retiming/capacity changes, simulate, evaluate,
revise, present cost-delay Pareto shortlist and export auditable evidence.
Human engineering approval precedes real implementation.

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

Reproduce one consultant/City corridor study before proposing changes; validate
against observed queues/travel times. Potential product: evidence preparation
and comparison workspace. Customer, willingness to pay, savings, procurement
and field effects remain unverified.
