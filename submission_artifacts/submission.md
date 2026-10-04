# Submission Header

## 1. Team NameBottleneck Busters

## 2. Team Member Names and GitHub Handles
- Abdelrahman Ahmed Ali Ahmed (@AbdelrahmanSuliman)
- Amy Miller (@Amesandfire)
- Praneetha Rajupalepu (@PraneethaRajupalepu)
- Reza Ardestani (@Reza-Ardestani)
- Sumit Gupta (@sumitgupta477)

## 3. Project Stream
Energy and Infrastructure Systems

## 4. Case Title
Custom Case — Which Calgary bottlenecks keep us stuck?

## 5. Project Short Description (3 lines max)
Bottleneck Busters helps Calgary mobility planners investigate traffic disruptions and compare interventions within budget.
An agent simulates signal and road-capacity changes, revises plans, and explains delay and cross-street tradeoffs with auditable evidence.
Improvements are modeled in simulation, not field-proven.

# Submission Details

## 1. Introduction and problem statement

Bottleneck Busters was inspired by our teammate Amy Miller, who has lived in Calgary for nearly a decade and recently experienced traffic congestion firsthand. Our [discovery conversations with Leah and Trevor](../validation_market_research/README.md) highlighted the need to distinguish recurring bottlenecks from temporary construction disruption and justify investments through clear costs, public impacts, assumptions, and tradeoffs. We ask: **which changes could reduce delay within budget without making cross-street travel worse?** Our agent-assisted lab uses City disruption records to guide investigation, simulates signal and road-capacity alternatives, revises proposals, and presents auditable evidence for planners. Results are modeled on a synthetic corridor, not field-proven, and require calibration and engineering review.

## 2. User Journeys 

1. **Monitor the city and selected areas.** Users explore Calgary's intersection map, live City-reported incidents and closures, and historical disruption patterns. They filter by area or road to identify locations worth investigating; these records provide disruption context rather than direct measurements of congestion.

2. **Configure budgets, assumptions, and intervention options.** Users set the available budget, traffic demand, estimated intervention costs, and cross-street protection limits, then select changes to test, such as signal retiming or added road capacity. Material and equipment availability are planned extensions; future integrations with cost, inventory, and maintenance APIs could streamline these inputs.

3. **Find, test, and justify an intervention — the core journey.** Users prioritize reported disruption hotspots using historical evidence and machine-learning forecasts, then run SUMO simulations to compare interventions against the same reference scenario. The agent evaluates delay, budget, and cross-street tradeoffs, revises unsuitable proposals, and explains the best feasible modeled option with an auditable report. Forecasts support investigation; simulation results support intervention comparison, with engineering review required before implementation.

## 3. Architecture and Design


## 4. Dataset


## 5. Result


## 6. Challenges and future works.
