.PHONY: setup api web test build refresh disruptions collect collect-loop mcp mcp-http mcp-image dev dev-check db-up db-sync dev-timescale architecture
setup:
	cd backend && uv sync --frozen
	cd frontend && npm ci
api:
	cd backend && uv run uvicorn app.api:app --host 127.0.0.1 --port 8008
web:
	cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
architecture:
	python3 scripts/check_architecture.py
	cd frontend && npm run architecture
test: architecture
	cd backend && uv run --group mcp pytest -q
	cd backend && uv run ruff check app tests ../scripts
build:
	cd frontend && npm run build
refresh:
	python3 scripts/refresh_incidents.py
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
	uv run --project backend --env-file .env.timescale python scripts/dev.py
mcp:
	cd backend && uv run --group mcp python -m app.mcp_server
mcp-http:
	cd backend && uv run --group mcp python -m app.mcp_server --transport streamable-http --host 127.0.0.1 --port 8000
mcp-image:
	docker buildx build --platform linux/arm64 -f backend/Dockerfile.mcp -t calgary-disruptions-mcp --load .
dev:
	python3 scripts/dev.py
dev-check:
	python3 scripts/dev.py --check
