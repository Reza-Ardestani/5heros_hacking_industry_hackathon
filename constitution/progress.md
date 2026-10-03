# Progress

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
