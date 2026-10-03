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

## Later

Measured CalTRACS profile/calibration and clearance times; inspected OSM network/signal
mappings; redirect-to-parallel-route option; evaluate Chronos-2 as a fourth forecaster in
the same validation/test harness; overdispersed forecast ranges; managed database and
scheduled collector for cloud use; AgentCore image build and deployment with inbound auth;
surrogate optimization; durable jobs; consultant pilot. RL only after a calibrated
training/evaluation environment.

## Event gates

Updated Discord topic deadline: Saturday October 3 noon MDT;
[exact evidence](../organizer_docs/discord/README.md). Team notification observed;
custom-case validation open. Final submission Sunday October 4 noon MDT.
No outgoing messages, deployment or final submission performed by this build.
