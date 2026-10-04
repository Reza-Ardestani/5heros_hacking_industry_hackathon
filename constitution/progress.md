# Progress

October 3 (design/product docs): shared React design tokens and gallery verified;
root [UJ_US](../UJ_US/README.md) now holds three journeys, profiles and 18 foldered
stories. Resource eligibility is a draft, not a new integration. Editable PowerPoint
template and newer organizer guidance captured; no organizer approval claimed.

October 3: early local prototype implemented and verified. Guided four-step UI,
actual SUMO policy-agent loop, cost/guardrail comparison and report export work.
12 backend tests and frontend build passed; synthetic model/default demand,
CalTRACS calibration and organizer acceptance remain open.
[Detailed evidence](../specs/features/phase-1-hackathon-mvp/progress.md).

October 3 (later): six-month Calgary disruption dataset (8 City sources, 3,987
incidents, 271 closures; JSON + Excel), Intersections view with live City feed and
area/route/lane prediction backtested against a flat baseline. 17 tests pass.
[Detailed evidence](../specs/features/phase-2-disruption-context/progress.md).

October 3 (database/MCP): disruption data moved into SQLite with a collector
(incremental polls, live sightings, closure removals, travel-time series) and a
10-tool MCP server (stdio + stateless HTTP for AgentCore). 22 tests pass.

October 3 (intersection studies): explainable decisions (lowest-delay option and the
rule that rejected it), every study logged to new database tables, incident-aware SUMO,
four new options (signal, clearance, turn bay, turn ban) weighted by six months of
incident frequency, per-intersection seconds of delay per incident, evidence summary.
28 tests pass. [Detailed evidence](../specs/features/phase-3-intersection-studies/progress.md).

October 3 (forecasting, MCP info, area focus): LightGBM (Poisson, native API) added as a
third forecaster; models chosen on validation days and scored on unseen test days
(LightGBM best on test in 5 of 11 standard selections, Bayes 3, flat 3). MCP server
self-description `/mcp-info` with live self-check (10 safe tools ok, 4 described but not
run) mirrored at `/api/mcp-info`. Click any map dot to focus a 0.5–2 km area; list,
prediction and the new `mcp-info-ml` tab follow it. 33 tests pass.

October 3 (chat assistant): chat dock at the bottom of every page answers with the MCP
tools (in-process) and navigates the app; built-in mode by default, optional Claude mode
with a user-supplied key. 47 tests pass.
[Detailed evidence](../specs/features/phase-4-chat-assistant/progress.md).
