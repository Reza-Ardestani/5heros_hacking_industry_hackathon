# Tech stack

Selected October 3 for authorized early MVP: Python 3.12+, uv lock;
FastAPI/Uvicorn; SUMO via eclipse-sumo; React/Vite/TypeScript + npm lock;
pytest for meaningful domain/API/real-simulation tests. Local attributed JSON
snapshots; transient bounded jobs. No DB, RL training or external LLM required.

Backend domain/application/infra/API boundaries explicit; frontend presentation;
SUMO owns numbers. Public data distinct from assumed flow/geometry/costs.
Credentials ignored; source versions/SHA256/units recorded. Commands in README
only after verification. No RadarCX runtime/database/deployment settings copied.
