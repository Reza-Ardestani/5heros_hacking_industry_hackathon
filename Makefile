.PHONY: setup api web test build refresh disruptions collect collect-loop mcp mcp-http mcp-image
setup:
	cd backend && uv sync --frozen
	cd frontend && npm ci
api:
	cd backend && uv run uvicorn app.api:app --host 127.0.0.1 --port 8008
web:
	cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
test:
	cd backend && uv run --group mcp pytest -q
	cd backend && uv run ruff check app tests ../scripts
build:
	cd frontend && npm run build
refresh:
	python3 scripts/refresh_incidents.py
disruptions:
	uv run --no-project --with openpyxl --with tzdata python scripts/build_disruption_dataset.py
collect:
	uv run --no-project --with tzdata python scripts/collect_disruptions.py
collect-loop:
	uv run --no-project --with tzdata python scripts/collect_disruptions.py --every 300
mcp:
	cd backend && uv run --group mcp python -m app.mcp_server
mcp-http:
	cd backend && uv run --group mcp python -m app.mcp_server --transport streamable-http --host 127.0.0.1 --port 8000
mcp-image:
	docker buildx build --platform linux/arm64 -f backend/Dockerfile.mcp -t calgary-disruptions-mcp --load .
