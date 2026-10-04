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

Bottleneck Busters began with a problem close to home. Our teammate Amy Miller has lived in Calgary for nearly a decade and has recently experienced traffic congestion firsthand. Her experience prompted our team to ask: **which Calgary bottlenecks should planners investigate, and which changes could reduce delay within a realistic budget without making cross-street travel worse?**

The challenge extends beyond identifying a busy intersection. Planners and budget reviewers need to compare alternatives, explain their costs and tradeoffs, and justify why one intervention deserves investment. A signal change may improve an arterial while increasing delay on side streets; adding road capacity may reduce modeled delay but exceed the available budget. Recurring problems also need to be distinguished from temporary disruption caused by construction and from locations where improvements are already underway.

Our [discovery research](../validation_market_research/README.md) helped sharpen this problem. In our conversation with Leah, she emphasized separating construction-related congestion from recurring bottlenecks and defining success through time savings, throughput, cost, and useful investment life. Trevor's [follow-up feedback](../validation_market_research/sources/colleague_response.txt), based on his experience within the City, emphasized comparing alternatives, public impacts, risks, costs, and timing. He also highlighted the need to expose source data, assumptions, limitations, and sensitivity so decision makers can understand why an option is recommended. These conversations informed our design; they do not establish City endorsement or verified demand for the product.

Our response is an agent-assisted planning lab for Calgary mobility planners. It uses attributed City incident and closure records to guide investigation, then tests signal and road-capacity alternatives against the same reference scenario. The agent evaluates modeled delay, budget, and cross-street constraints, revises an unsuitable proposal, and produces an auditable comparison for human review. City incident records describe reported disruptions; they do not directly measure congestion or delay. Our prototype uses a synthetic corridor and explicit demand and cost assumptions, so its improvements are simulation results requiring calibration and engineering review before real-world use.

## 2. User Journeys 


## 3. Architecture and Design


## 4. Dataset


## 5. Result


## 6. Challenges and future works.
