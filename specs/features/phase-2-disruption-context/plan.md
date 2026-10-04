# Plan

1. Discover City feeds behind the traffic-camera page via the data.calgary.ca catalog.
2. Pure rules (`domain/disruption_rules.py`, `domain/geo.py`, `domain/forecast.py`).
3. Ingest (`application/disruption_ingest.py`): records, enrichment, summary.
4. Storage and collection: `infra/city_open_data.py` (paginate/retry/hash),
   `infra/disruption_store.py` (SQLite), `application/disruption_collector.py`
   (backfill/collect/seed). Scripts `build_disruption_dataset.py` (backfill + export)
   and `collect_disruptions.py` (poll, `--every`).
5. Read service `application/disruptions.py` used by `api.py` and `mcp_server.py`.
6. Frontend: Intersections view and prediction panel.
7. `backend/Dockerfile.mcp` for AgentCore (ARM64, 0.0.0.0:8000/mcp).
8. Tests, lint, build, browser and MCP-over-HTTP verification; record evidence.

Commands:

```sh
make disruptions      # backfill + export
make collect          # one poll; make collect-loop for every 5 minutes
make mcp | make mcp-http | make mcp-image
make test             # includes MCP tests (uv --group mcp)
cd frontend && npm run build
```

`frontend/vite.config.ts` reads optional `API_URL` for the dev proxy (default
unchanged, port 8008) so a second local API can back a second dev server.
Design: [DES-BB-002](../../../docs/design/disruption-data/design.md).
