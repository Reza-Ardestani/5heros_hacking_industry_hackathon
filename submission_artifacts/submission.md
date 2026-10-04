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

The Python/FastAPI backend follows **clean architecture**: domain rules and application use cases depend on explicit interfaces, while infrastructure adapters handle City data, databases, SUMO, MCP tools, and optional chat providers. Dependencies are wired at entry points, keeping planning rules separate from external services. HTTP and MCP expose shared application services; the agent proposes interventions, evaluates SUMO trials, and revises plans against budget and cross-street constraints. SQLite provides the durable write journal and fallback, with an optional TimescaleDB mirror for synchronized reads.

The React/TypeScript frontend uses **vertical slices** for studies, intersections, forecasting, assistant, and storage. Each feature owns its UI, API calls, types, and tests; shared transport, formatting, and design tokens support the slices, while the app shell manages navigation and composition. This keeps related behavior together and allows features to evolve independently. The diagram illustrates the Codespaces demo layout; the same components also run locally.

[![Bottleneck Busters system architecture](https://raw.githubusercontent.com/Reza-Ardestani/5heros_hacking_industry_hackathon/main/submission_artifacts/06-architecture.png)](https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon/blob/main/submission_artifacts/06-architecture.png)

Detailed design: [Backend clean architecture](https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon/blob/main/docs/design/clean-architecture.md) · [Frontend vertical slices](https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon/blob/main/docs/design/frontend-vertical-slices.md).

Deployment setup, restart commands, port sharing, and persistence limits are documented in the [repository deployment guide](https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon/blob/main/README.md#deployment-guide). The shared demo runs in GitHub Codespaces, serving the built frontend and API together on port 8080 behind a demo login.

## 4. Dataset

We use six months of [Traffic Incidents (unofficial archive)](https://data.calgary.ca/d/35ra-9556), alongside live [Current Traffic Incidents](https://data.calgary.ca/d/4jah-h97u) and [Construction Detours](https://data.calgary.ca/d/w8zq-79bq). Supporting City datasets provide [signals](https://data.calgary.ca/d/qr97-4jvx), [cameras](https://data.calgary.ca/d/k7p9-kppz), [2024 traffic volumes](https://data.calgary.ca/d/cauu-7hnw), [travel times](https://data.calgary.ca/d/aeb8-fh2w), and [road construction projects](https://data.calgary.ca/d/sizs-hgef). The committed April–early October 2026 exports contain **3,989 deduplicated incidents and 270 closures**; they describe reported disruptions, not direct measurements of congestion or intervention benefits. Contains information licensed under the Open Government Licence – City of Calgary ([terms](https://data.calgary.ca/stories/s/Open-Calgary-Terms-of-Use/u45n-7awa)).

## 5. Methods and Algorithms

| Method | Used for |
|---|---|
| Empirical Bayes and LightGBM, compared with a flat-average baseline | Forecasting reported incident counts; rolling validation selects the model |
| Negative-binomial intervals | Showing uncertainty around incident forecasts |
| Bayesian priority ranking and Benjamini–Hochberg correction | Shortlisting corridors/intersections and screening recent changes |
| SUMO with paired arrival inputs | Comparing modeled delay, cross-street impacts, and trip completion against a reference |
| Rule-based propose–evaluate–revise loop | Revising signal plans and choosing the lowest-delay tested option within budget and cross-street limits |
| Pareto analysis and sensitivity checks | Explaining cost/delay tradeoffs and testing ±20% demand and −50% to +50% costs/budget |

Forecasting guides investigation; simulation evaluates interventions. The planning loop uses coded policies, with optional LLM assistance confined to chat.

## 6. Result

In the [recorded synthetic SUMO experiment](https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon/blob/main/docs/demo/example_result.json), the agent rejected its first signal proposal for excessive cross-street delay, then revised it to achieve **27.17% less total modeled delay** than the equal-green reference. Cross-street delay rose **14.80%**, within the 30% guardrail; the assumed CAD 15,000 intervention fit the CAD 100,000 budget, and both ±20% demand checks passed. Separately, a [current-code citywide forecast backtest](https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon/blob/main/docs/demo/forecast_snapshot_result.json) on September 4–October 2 selected empirical Bayes: daily mean absolute error **6.116 versus 6.856 incidents** for the flat baseline, a **10.8% reduction**. These are retrospective forecasting and simulated intervention results, not field-proven Calgary savings.

**Budget-responsive recommendations:** In the team's [demo video](https://youtu.be/mJIJ2JE7_00), increasing the budget to **CAD 5 million** made an extra-lane intervention eligible and the planner recommended it. Changing the budget changes which estimated-cost options are feasible; the tool chooses the lowest modeled delay among options that also meet cross-street and trip-completion constraints. This illustrates scenario-based decision support, not a guarantee of real-world accuracy; the video scenario is separate from the CAD 100,000 experiment above.

## 7. Challenges and future works.

Our main challenges are calibrating the synthetic simulation with measured Calgary traffic counts and signal timings, validating forecasts on fresh data and sparse intersections, and verifying intervention costs and feasibility. Next steps include integrating material, equipment, and maintenance APIs; improving forecast uncertainty; making simulation jobs durable; and piloting the workflow with transportation planners. Real-world interventions will require engineering review, including safety, pedestrian impacts, and construction constraints.

## 8. Live webapp and demo

1. **Live webapp:** [Open Bottleneck Busters](https://bottleneck-busters-main-6xv7jvg66wh455x-8080.app.github.dev/). **Username:** `bottleneck` · **Password:** `XX5DIh2lfEFo`.
2. **Live demo:** [Watch the demo video](https://youtu.be/mJIJ2JE7_00).

## Appendix:

**GitHub repository:** [Bottleneck Busters — source code, architecture, and run instructions](https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon).

**Project screenshots:**

1. [Planning workspace](https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon/blob/main/submission_artifacts/01-planning-workspace.jpg)
2. [Intervention design](https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon/blob/main/submission_artifacts/02-intervention-design.jpg)
3. [Agent simulation](https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon/blob/main/submission_artifacts/03-agent-simulation.jpg)
4. [Recommendation comparison](https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon/blob/main/submission_artifacts/04-recommendation-comparison.jpg)
5. [Calgary intersections](https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon/blob/main/submission_artifacts/05-calgary-intersections.jpg)
