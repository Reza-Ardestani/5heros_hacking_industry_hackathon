# Architecture

FastAPI modular monolith + separate React frontend + SUMO subprocess adapter.
Domain rules independent of HTTP/UI/provider; application coordinates tools;
infrastructure owns IO; API validates bounded inputs and composes dependencies.

[Design](../docs/design/bottleneck-lab/design.md), [catalog](../docs/modeling.md).
This separate product chooses the root UJ_US/ tree for canonical journeys,
individually foldered stories and supporting client profiles (user request October 3).
Legacy docs/user_journeys and docs/user_stories paths redirect to the new home.
RCX modeling catalog provides structural precedent; customer validation stays explicit.
Diagrams under docs/diagrams; specs exactly four files. Organizer originals unchanged.

Database scope (amended October 3 at the user's request): disruption context only,
in local SQLite behind infra/disruption_store.py; an MCP server and the HTTP API share
one application service. RadarCX schema/RLS/timestamp policies are not transplanted.
Simulation jobs stay transient, bounded, local only; restart loses their history.
[Disruption data design](../docs/design/disruption-data/design.md). Real-world change requires engineering
review and calibration. Numerical results must originate in simulator outputs.
