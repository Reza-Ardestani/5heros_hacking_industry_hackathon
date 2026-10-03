# Judge brief — Bottleneck Busters

## One-sentence product

An agent-assisted corridor study workspace that runs, critiques and revises
traffic intervention simulations, then exports a cost-aware recommendation
with its assumptions and rejected alternatives.

## User, trigger and proposed pain

Our candidate user is a transportation engineer or consultant study lead asked
to compare retiming with added capacity before a program/budget review. The
pain we are testing is repeated comparison and evidence preparation across that
handoff. A program reviewer is the second user; travelers are beneficiaries.
[ICP](../product_research/ideal_client_profile.md).

Calgary already operates connected signals and formal investment planning.
Professional optimization/simulation tools exist. Our proposed contribution is
the constrained tool loop and reviewable evidence workflow; superiority over
existing tools and customer time savings remain unvalidated.
[Primary-source research](../product_research/evidence.md).

## Concrete demonstration

Use the guided walkthrough: frame the decision; set budget and cross-street
guardrail; run actual SUMO; review the recommendation and export its evidence.
The planner proposes a demand-based signal split, reads actual simulator
outcomes, revises the split, and compares a separately costed capacity option.
Deterministic policy agents perform this loop; there are no LLM calls or trained RL.

Recorded default experiment, not a Calgary field result:

| Option | Modeled total delay reduction | Cross mean delay change | Assumed capital | Decision |
|---|---:|---:|---:|---|
| Equal-green reference | 0% | 0% | $0 | Feasible fallback |
| Demand-based retiming | 72.61% | +88.96% | $15,000 | Reject: exceeds 30% cross-street guardrail |
| Outcome-based revision | 27.17% | +14.80% | $15,000 | Selected within $100,000 budget |
| Added arterial lane | 59.06% | −1.24% | $1,200,000 | Reject: exceeds budget |

[Actual recorded report](example_result.json). Read current results during a live
run; edited inputs can change the recommendation. Same arrivals within each
seed support fair comparisons. Three seeds select the recommendation; these do
not provide an independent confirmatory estimate. Demand stress checks are
sensitivity experiments, not measured future traffic predictions.

## What is proven, what remains open

**Demonstrated locally:** separate frontend/API, native simulation execution,
outcome-based revision, budget/service checks, explicit failures, visual playback,
cost-delay comparison and JSON report. See [implemented stories](../user_stories/planning.md).

**Still open:** customer pain, willingness to pay, calibrated Calgary geometry/
timings/flows, multimodal constraints, engineering cost estimates, field benefits,
production deployment and organizer case acceptance. Incident data is real
context; it does not drive demand or identify the best corridor. Default geometry,
arrivals and costs are synthetic/assumed. Imported arrivals alone do not calibrate
the model. Maintenance funding prioritization is outside the current product.

## Suggested opening, about 30 seconds

> Before changing a corridor, an engineer must explain which alternative is worth
> studying and why others fail the constraints. We built a working loop that
> simulates a proposal, checks its outcomes, revises it, and packages the evidence.
> Today's demonstration uses a labeled synthetic corridor with Calgary incident
> context. Next we will test the workflow with practitioners and reproduce one
> observed corridor study before making any road-benefit claim.

## Answering the two hardest questions

**Why not existing engineering software?** It already optimizes and simulates.
We are testing whether this guided revision/report workflow removes recurring
work for a specific team. No comparative productivity benchmark yet.

**Who will buy?** Proposed sponsors are municipal mobility program owners or
consulting practice leads. Start with a supervised study pilot; buyer, procurement
route and pricing need discovery. We have no customer or City endorsement.

Use [demo script](demo_script.md) for five-minute timing and
[discovery plan](../product_research/discovery_plan.md) for the next evidence step.
