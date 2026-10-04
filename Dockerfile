# Single container: FastAPI serves /api and the built React app on $PORT.
FROM node:22-slim AS web
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . /app
COPY --from=web /src/frontend/dist /app/frontend/dist
# data/ must stay writable: later branches keep a SQLite store and run logs there.
RUN useradd --system --uid 10001 app && chown -R app /app/data
USER app
ENV PATH=/app/backend/.venv/bin:$PATH BB_REQUIRE_AUTH=1 PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn app.deploy:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
