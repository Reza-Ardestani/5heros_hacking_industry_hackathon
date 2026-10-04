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
Simulation jobs stay transient, bounded, local only; restart loses their history,
but every study's actions, options and trials are also written to sim_* tables and
data/runs/*.jsonl. Forecasting lives in the pure domain (`domain/forecast.py`,
`domain/ml_forecast.py`): flat, Bayesian and LightGBM models share one interface and are
chosen on validation days before test scoring. The MCP server describes itself at
`/mcp-info` (built from its live tool list) and the API mirrors it at `/api/mcp-info`.
[Disruption data design](../docs/design/disruption-data/design.md). Real-world change requires engineering
review and calibration. Numerical results must originate in simulator outputs.

Storage amendment, user-authorized October 4: keep application/domain APIs intact.
SQLite owns local atomic writes and a transactional outbox; the Timescale adapter
replicates ordered row changes and a checkpoint in one PostgreSQL transaction.
API/MCP/collectors share this boundary. Reads prefer the caught-up Timescale mirror,
otherwise use SQLite and expose degradation/backlog. A persisted source identity
prevents mixing independent SQLite writers in the same PostgreSQL destination.
Existing SQLite rows bootstrap locally without re-downloading City data. Neither
database credentials nor raw connection errors are returned to callers.
[Design](../docs/design/timescale-sqlite/design.md),
[diagram](../docs/diagrams/storage_failover.md),
[spec](../specs/features/timescale-sqlite-backends/requirements.md).

October 4 user-authorized architecture refactor: domain/application dependencies
point inward; storage, City feeds, tool execution and chat providers use explicit
ports wired at entry points. Infrastructure owns export seeding, run logs and SDK
implementations. Pydantic scenario contracts and process-local caches/jobs remain
intentional hackathon compromises. Preserve existing API/MCP/numerical contracts.
[Spec](../specs/features/clean-architecture-boundaries/requirements.md).

October 4 user-authorized frontend vertical slices: studies, intersections,
forecasting, assistant and storage own UI, API calls, types and feature tests.
App handles navigation/composition; cross-slice imports use public index.ts
entry points. Shared transport/formatting/navigation/area contracts and design
tokens import no features. No additional state framework or API contract change.
[Spec](../specs/features/frontend-vertical-slices/requirements.md).
