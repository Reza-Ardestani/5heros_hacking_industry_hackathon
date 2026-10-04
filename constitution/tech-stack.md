# Tech stack

Selected October 3 for authorized early MVP: Python 3.12+, uv lock;
FastAPI/Uvicorn; SUMO via eclipse-sumo; React/Vite/TypeScript + npm lock;
pytest for meaningful domain/API/real-simulation tests. Local attributed JSON
snapshots; transient bounded jobs. No RL training or external LLM required.

Amended October 3 at the user's request: Calgary disruption data is stored in
SQLite (standard library, one local file at data/db/, git-ignored, rebuilt or
seeded from committed exports). The official `mcp` Python SDK is an optional
dependency group for the agent tool server. Simulation jobs remain transient.

Backend domain/application/infra/API boundaries explicit; frontend presentation;
SUMO owns numbers. Public data distinct from assumed flow/geometry/costs.
Client decision reaffirmed October 3: React/Vite/TypeScript web app for the
desktop-first planner and reviewer journeys. Responsive browser layouts remain;
no native mobile application is planned. The [target C4 diagram](../docs/diagrams/top_level_architecture.html)
uses React web; TimescaleDB remains a target, distinct from the current SQLite store.
Credentials ignored; source versions/SHA256/units recorded. Commands in README
only after verification. No RadarCX runtime/database/deployment settings copied.
