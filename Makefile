.DEFAULT_GOAL := help
PYTHON ?= python3
DEV_ARGS ?=

.PHONY: help setup api web test test-backend test-web build refresh disruptions collect collect-loop mcp mcp-http mcp-image dev dev-check db-up db-sync dev-timescale architecture
help:
	@printf '%s\n' \
	  'Bottleneck Busters — run commands from repository root' \
	  '  make dev             Install dependencies; start API + frontend + MCP (Ctrl+C stops all)' \
	  '  make setup           Install locked backend and frontend dependencies' \
	  '  make api             Start backend at http://127.0.0.1:8008' \
	  '  make web             Start frontend at http://127.0.0.1:5173 (second terminal)' \
	  '  make dev-check       Start services, smoke-check endpoints, then stop' \
	  '  make test-backend    Run backend pytest suite' \
	  '  make test-web        Run frontend tests and slice guard' \
	  '  make architecture    Check backend and frontend dependency boundaries' \
	  '  make test            Run architecture guards, backend tests and Ruff' \
	  '  make build           Build frontend production bundle' \
	  '  make collect         Poll City data once; collect-loop repeats every 5 minutes' \
	  '  make disruptions     Backfill six months and export JSON/XLSX (network required)' \
	  '  make refresh         Refresh incident snapshot (stop API first)' \
	  '  make mcp             Start MCP over stdio; mcp-http uses port 8000' \
	  '  make db-up           Start optional TimescaleDB (Docker + .env.timescale required)' \
	  '  make db-sync         Replay local history into TimescaleDB' \
	  '  make dev-timescale   Start services using .env.timescale' \
	  '  Override launcher flags: make dev DEV_ARGS="--api-port 8108 --web-port 5273 --mcp-port 8100"' \
	  '  Override Python command: make dev PYTHON=python'
setup:
	cd backend && uv sync --frozen
	cd frontend && npm ci
api:
	cd backend && uv run uvicorn app.api:app --host 127.0.0.1 --port 8008
web:
	cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
architecture:
	$(PYTHON) scripts/check_architecture.py
	cd frontend && npm run architecture
test: architecture
	cd backend && uv run --group mcp pytest -q
	cd backend && uv run ruff check app tests ../scripts
test-backend:
	cd backend && uv run --group mcp pytest -q
test-web:
	cd frontend && npm test
build:
	cd frontend && npm run build
refresh:
	$(PYTHON) scripts/refresh_incidents.py
disruptions:
	cd backend && uv run --with openpyxl python ../scripts/build_disruption_dataset.py
collect:
	cd backend && uv run python ../scripts/collect_disruptions.py
collect-loop:
	cd backend && uv run python ../scripts/collect_disruptions.py --every 300
db-up:
	docker compose --env-file .env.timescale -f compose.timescale.yml up -d --wait --wait-timeout 60
db-sync:
	cd backend && uv run --env-file ../.env.timescale python ../scripts/sync_storage.py
dev-timescale:
	uv run --project backend --env-file .env.timescale python scripts/dev.py $(DEV_ARGS)
mcp:
	cd backend && uv run --group mcp python -m app.mcp_server
mcp-http:
	cd backend && uv run --group mcp python -m app.mcp_server --transport streamable-http --host 127.0.0.1 --port 8000
mcp-image:
	docker buildx build --platform linux/arm64 -f backend/Dockerfile.mcp -t calgary-disruptions-mcp --load .
dev:
	$(PYTHON) scripts/dev.py $(DEV_ARGS)
dev-check:
	$(PYTHON) scripts/dev.py --check $(DEV_ARGS)
