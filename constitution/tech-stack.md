# Tech stack

Selected October 3 for authorized early MVP: Python 3.12+, uv lock;
FastAPI/Uvicorn; SUMO via eclipse-sumo; React/Vite/TypeScript + npm lock;
pytest for meaningful domain/API/real-simulation tests. Local attributed JSON
snapshots; transient bounded jobs. No RL training or external LLM required.

Amended October 3 at the user's request: Calgary disruption data is stored in
SQLite (standard library, one local file at data/db/, git-ignored, rebuilt or
seeded from committed exports). The official `mcp` Python SDK is an optional
dependency group for the agent tool server. Simulation jobs remain transient.
Forecasting adds LightGBM (MIT, native API, with NumPy/SciPy) as a competing model; it is
used only when it wins on validation days against the flat baseline and Bayesian rates.
No pretrained or hosted models (Hugging Face, LLM APIs) are used; Chronos-2 is a candidate
to evaluate later in the same harness. Cloud Run deployment files were added by a teammate
(`Dockerfile`, `.github/workflows/deploy.yml`, `deploy/`); the MCP image is
`backend/Dockerfile.mcp`.

Amended October 3 at the user's request (chat dock): `mcp` moves to the main
dependencies because the API now calls the MCP tools in-process for the chat. The
`anthropic` SDK is added for an optional Claude mode that runs only when the operator
sets `ANTHROPIC_API_KEY`; the default built-in mode needs no LLM, key or network, so
"no external LLM required" still holds. Chat never writes to the database.

Backend domain/application/infra/API boundaries explicit; frontend presentation;
SUMO owns numbers. Public data distinct from assumed flow/geometry/costs.
Client decision reaffirmed October 3: React/Vite/TypeScript web app for the
desktop-first planner and reviewer journeys. Responsive browser layouts remain;
no native mobile application is planned. The [target C4 diagram](../docs/diagrams/top_level_architecture.html)
uses React web; its TimescaleDB target is selected in the October 4 storage amendment below.
Credentials ignored; source versions/SHA256/units recorded. Commands in README
only after verification. No RadarCX runtime/database/deployment settings copied.

Selected October 4 by the user: TimescaleDB (PostgreSQL extension) with psycopg 3,
plus the existing SQLite store as a durable local write journal and fallback.
`BB_DB_BACKEND=timescale` enables the mirror; SQLite remains the default without
configuration. Healthy, caught-up reads use TimescaleDB; writes commit locally
before replication. PostgreSQL travel-time samples use a TIMESTAMPTZ hypertable.
Both database volumes must persist across app/container replacement. This is a
single shared SQLite volume design, not cross-host high availability.
[Spec](../specs/features/timescale-sqlite-backends/requirements.md).
