# Roadmap

## Phase 1 — early working prototype

[Spec](../specs/features/phase-1-hackathon-mvp/requirements.md): organizer evidence,
problem/modeling, separate backend/frontend, incident snapshot, SUMO scenario,
cost-aware constrained revision loop, comparison/export, local verification.
User authorized October 3. External organizer validation unverified.

## Phase 2 — Calgary disruption context (done October 3)

[Spec](../specs/features/phase-2-disruption-context/requirements.md): six months of City
open data in SQLite with a collector, Intersections view with live feed, area/route/lane
forecasts (flat baseline, Bayesian rates, LightGBM chosen on validation days), MCP server
with `/mcp-info` self-description and self-check.

## Phase 3 — intersection studies (done October 3)

[Spec](../specs/features/phase-3-intersection-studies/requirements.md): explainable
decisions, every study logged to database tables, incident-aware SUMO, signal /
clearance / turn-bay / turn-ban options weighted by observed incident frequency,
seconds of delay per incident, evidence summary, click-a-dot area focus and the
`mcp-info-ml` tab.

## Phase 4 — chat assistant (done October 3)

[Spec](../specs/features/phase-4-chat-assistant/requirements.md): bottom chat dock that
answers with the MCP tools and moves the UI (pages, intersections, quadrant, prediction
panel, `mcp-info-ml`, intersection studies); built-in by default, Claude optional.

## Selected October 4 — dual storage

User authorized [TimescaleDB with SQLite fallback](../specs/features/timescale-sqlite-backends/requirements.md).
Implement after constitution/spec: durable local journal, ordered replication,
time-series hypertable, offline migration, health reporting, persistent DB volume,
SQLite regression and real Timescale outage/recovery verification. No production
deployment or multi-host failover implied by local implementation.

## October 4 — architecture boundaries

User-authorized backend clean dependency boundaries and frontend vertical slices
implemented locally. Frontend capability ownership, lifecycle state and public
entry points verified by tests/build and import guards.
[Frontend spec](../specs/features/frontend-vertical-slices/requirements.md),
[backend spec](../specs/features/clean-architecture-boundaries/requirements.md).

## Later storage and modeling work

October 4 user-authorized repository health corrections: fix confirmed launcher,
lint and documentation defects while preserving the submitted issue and
submission_artifacts/submission.md. No product behavior/model changes planned.
[Spec](../specs/features/repository-health/requirements.md).

October 4 user-authorized README/demo onboarding: present the problem, journeys,
architecture images, datasets and bounded results using the submission structure;
finish with verified Makefile commands for separate or combined API/UI startup.
[Spec](../specs/features/readme-demo-onboarding/requirements.md).

Measured CalTRACS profile/calibration and clearance times; inspected OSM network/signal
mappings; redirect-to-parallel-route option; evaluate Chronos-2 as a fourth forecaster in
the same validation/test harness; overdispersed forecast ranges; managed database and
scheduled collector for cloud use; AgentCore image build and deployment with inbound auth;
surrogate optimization; durable jobs; consultant pilot. RL only after a calibrated
training/evaluation environment.
User-requested [resource evidence draft](../specs/features/phase-4-resource-evidence/requirements.md):
dated labor/material/equipment availability and costs inform conditional intervention
eligibility. Provider access, resource requirements and engineering gates remain open.

Measured CalTRACS profile/calibration; inspected OSM network/signal mappings;
more physical interventions; surrogate optimization; durable jobs; consultant
pilot. RL only after calibrated training/evaluation environment.

## Event gates

Updated Discord topic deadline: Saturday October 3 noon MDT;
[exact evidence](../organizer_docs/discord/README.md). Team notification observed;
custom-case validation open. Final submission Sunday October 4 noon MDT.
No outgoing messages, deployment or final submission performed by this build.
