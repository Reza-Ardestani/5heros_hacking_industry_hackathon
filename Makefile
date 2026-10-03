.PHONY: setup api web test build refresh
setup:
	cd backend && uv sync --frozen
	cd frontend && npm ci
api:
	cd backend && uv run uvicorn app.api:app --host 127.0.0.1 --port 8008
web:
	cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
test:
	cd backend && uv run pytest -q
	cd backend && uv run ruff check app tests ../scripts
build:
	cd frontend && npm run build
refresh:
	python3 scripts/refresh_incidents.py
