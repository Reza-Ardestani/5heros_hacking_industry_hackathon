# S-BB-2 — Calgary disruption context, intersection explorer and prediction

Requested by the user October 3, 2026: parse the City traffic-camera/traffic-report
sources, collect at least six months of incidents and closures in all categories,
produce JSON and Excel for analysis, show intersection details in the UI with a
live example, and let the user choose area, route and lane to generate predictions.
Data reference: [data/analysis/README.md](../../../data/analysis/README.md).
Builds on [S-BB-1](../phase-1-hackathon-mvp/requirements.md); does not change the
SUMO simulation, its scenario contract or its recommendation logic.

FR-1 Reproducible download of at least 6 months of City incidents plus closures,
cameras, signals, travel times, projects and 2024 volumes; raw payloads hashed;
licence recorded.
FR-2 Every incident classified into a category/group, lane impact, lane position,
direction, period, corridor and intersection; rules published with the data.
FR-3 JSON outputs and an Excel workbook with record-level and aggregate sheets.
FR-4 API: summary, intersection list/detail, live City feed, selection options and
prediction endpoints; live feed degrades to last good response on network failure.
FR-5 UI "Intersections" view: live incidents/closures (auto-refresh), searchable
intersection list, overview map, detail with live camera image, category/lane/
direction/hour/weekday/month breakdowns, nearby closures and recent incidents.
FR-6 UI prediction panel: Area, Route, Direction, Lane, Incident type,
Intersection, horizon (1–28 days); expected count, 80% range, per-day × period
probabilities, backtest against a named baseline, likely types and locations.
FR-7 (added Oct 3, user request) Extracted data saved in a database: every download
logged with URL/SHA256/counts; idempotent upserts; seeded offline from exports.
FR-8 Automated collection of dynamic data: incremental polls, live sightings per
incident, closure removals, travel-time series, saved predictions; CLI one-shot/loop,
optional in-API thread, UI live panel persistence.
FR-9 Tools exposed through an MCP server (stdio + stateless streamable HTTP at /mcp)
suitable for Amazon Bedrock AgentCore Runtime, sharing the API's service layer.
TR-1 Forecast model and text rules are pure domain modules; I/O stays in infra;
database is stdlib SQLite; `mcp` SDK only in an optional dependency group.
TR-2 Every screen states that incidents are reported disruptions, not flow,
delay or crash risk; prediction verdict shown even when worse than baseline.

## Acceptance

AC-1 Window covers six complete months; counts reconcile (category = month = total).
AC-2 Excel opens with all sheets; JSON records carry provenance manifest.
AC-3 Endpoints tested; live endpoint tested offline.
AC-4 Prediction backtest reports model and baseline error on the same held-out days.
AC-5 Browser: list to detail, live link to detail, picker cascade to prediction,
detail to "Predict this intersection"; no failed API calls.
AC-6 Re-polling unchanged data inserts/updates nothing; failures recorded per dataset.
AC-7 Live incidents gain sightings across polls; closures leaving the feed are marked.
AC-8 MCP tools list with annotations and return the same data as the API, in-process
and over HTTP.

Out of scope: using incidents as simulation demand, citywide bottleneck ranking
claims, crash-risk modeling, persisted user selections, AWS deployment, managed DB.
