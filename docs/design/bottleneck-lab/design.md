# DES-BB-001 — Budget-aware traffic intervention lab

## Decisions settled October 3, 2026

User authorized early implementation and modeling/constitution/spec updates.
Topic notification verified; external organizer acceptance still open.

FastAPI modular monolith; separate React/Vite frontend; SUMO subprocess adapter.
Pure domain metrics/constraints; application orchestration; infrastructure owns
IO. No database/distributed workers/provider requirement. Backend local-only,
CORS loopback frontend; bounded transient jobs lost on restart.

First executable slice uses explicit synthetic three-intersection corridor and
arrival profile. Real incident snapshot is separate context; downloaded Calgary
OSM geometry is a source artifact, not disguised as calibrated model. Measured
profile import supports normalized directional arrivals with source metadata.
Actual CalTRACS export and inspected OSM movement/signal adapter remain next gate.

Agents are deterministic tool-using policies: diagnose demand imbalance, propose
bounded split, simulate, evaluate, revise from observed per-axis delay, stress test,
report. They are not LLM calls or trained models; organizer rubric explicitly
allows optimizer/simulation/automated revision. Optional LLM seam can propose
schema-valid actions; numerical evidence always comes from SUMO.

Reference equal green split; first candidate demand-proportional split; revision
uses measured main/cross delay; capacity option adds arterial lane. Hard bounds
preserve yellow/all-red clearance and cross-street service. No signal removal.
Budget and cross-street delay guardrail filter recommendations; report nondominated
cost/delay options. Hold-out seeds and ±20% demand stress separate from tuning.

Identical departures/input manifest across variants. Demand window then drain;
hard cap records unfinished/uninserted trips. Disable teleport; include departure
waiting and per-axis traffic time loss. No engine failure becomes success.

Costs/occupancy/value-of-time/operating-days are user estimates. Annualization is
illustrative, not field savings. Safety, constructibility, pedestrians, induced
demand and actual travel-time calibration remain qualified-engineer work.

[Architecture](../../diagrams/architecture.md), [sequence](../../diagrams/run_sequence.md).
Extend via network/demand/provider ports; durable jobs only when scale justifies.
RL deferred pending calibrated environment and meaningful training/evaluation.

## Guided experience — user steering October 3

User rejected the first UI and selected a guided walkthrough. Revised navigation:
frame the planning problem, define interventions/limits, run the simulation,
review the recommendation. Evidence/sources is a separate accessible view.

Start with the decision question and concrete user/constraints, then reveal costs
and protected cross-street delay. The simulation step shows actual positions and
current tool activity; the review step shows four options, paired delay bars,
constraint rejection and investment tradeoffs. Inputs can be edited after a run;
a stale-result notice prevents treating the old recommendation as updated.
No source-data or statistical limitation is hidden by the guided presentation.
