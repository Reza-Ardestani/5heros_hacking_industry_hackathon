# Architecture

FastAPI modular monolith + separate React frontend + SUMO subprocess adapter.
Domain rules independent of HTTP/UI/provider; application coordinates tools;
infrastructure owns IO; API validates bounded inputs and composes dependencies.

[Design](../docs/design/bottleneck-lab/design.md), [catalog](../docs/modeling.md).
This separate product chooses local canonical docs/user_journeys and docs/user_stories
for teammate portability; RCX modeling catalog provides structural precedent.
Diagrams under docs/diagrams; specs exactly four files. Organizer originals unchanged.

No DB: RadarCX schema/RLS/timestamp policies are not transplanted. Jobs transient,
bounded, local only; restart loses history. Real-world change requires engineering
review and calibration. Numerical results must originate in simulator outputs.
