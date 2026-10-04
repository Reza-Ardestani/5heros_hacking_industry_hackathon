# Progress — October 3, 2026

## Done

- Dataset built 2026-10-03 18:17 UTC: 8 City datasets, 6,762 source rows;
  3,987 incidents (4,070 raw, 83 duplicates) for 2026-04-01 to 2026-10-03;
  271 closures; 20-sheet workbook. Details: [data README](../../../data/analysis/README.md).
- Parser fixes found by spot checks: interchange volume mismatch (now same-road
  segment only), bare road names (Deerfoot to Deerfoot Trail aliasing), lane position.
- API: `/api/disruptions/summary`, `/intersections`, `/intersection?key=`, `/live`,
  `/options`, `/predict`. UI: Intersections view with live feed, map, camera,
  breakdowns and prediction panel.

## Validation evidence (Windows 11, uv-managed venv, Node build)

| Check | Result |
|---|---|
| `uv run pytest -q` | 17 passed (12 existing incl. real SUMO + 5 new) |
| `uv run ruff check app tests ../scripts`, `ruff format --check` | Passed |
| `npm run build` | Passed |
| Reconciliation | Category sum = monthly sum = 3,987 (asserted in test) |
| Workbook | 20 sheets present (openpyxl read-back) |
| Browser (Vite 5183 to API 8018) | Live incident "Eastbound 64 Avenue and 9 Street NE" linked to its intersection and scrolled to detail; live camera JPEG loaded; picker cascade SE, Deerfoot Trail, SB, Right lane produced 2.3 expected (0–4) with baseline verdict; detail "Predict this intersection" filled route + intersection; all `/api/*` requests 200 after API restart |
| Backtest, all Calgary | Daily MAE 6.12 vs 6.86 flat baseline (10.7% better); 80% range hit 60.7% (too narrow) |
| Backtest, single route/lane/intersection | Within ±5% of baseline: no demonstrated gain |

## Database, collector and MCP (later October 3)

Code review findings fixed: data only in static files (now SQLite); parsing rules
locked inside the script (now `domain/`); global alias state (now persisted meta);
archive/live identity mismatch (normalized `uid`); closure status frozen at build
(now evaluated at read time); live feed cached failures and O(n²) hotspot matching
(now never cached, grid index); forecast start after a gap day (now today); UI stale
responses (request guards); `EMS` substring match (word boundary); 18 distinct
closures merged by a too-coarse ID (description added; 271 rows → 270 closures, the
remaining pair is a true duplicate 25 m apart).

| Check | Result |
|---|---|
| `make disruptions` (real City API) | 8 datasets, 8 `fetch_runs` ok; 4,101 archive rows → 4,017 incidents stored (3,987 in window); 270 closures; 68 travel times; DB 12.5 MB |
| `make collect` twice | Second poll: 0 inserted, 0 updated for every dataset; 44 archive rows re-read, 0 changed |
| Live persistence | UI/MCP live call stored a new incident (`source=live`); sightings recorded; status shows 2 incidents seen live |
| `uv run --group mcp pytest -q` | 22 passed (12 S-BB-1 incl. real SUMO + 10 S-BB-2) |
| `ruff check`, `ruff format --check`; `npm run build` | Passed |
| MCP over streamable HTTP (stateless, client probe) | initialize, list 10 tools, `predict_disruptions` (Deerfoot 14.54, 10–20), `get_live_disruptions` (persisted), `get_data_status` |
| Browser after DB switch | Live panel "saved to database"; predictions unchanged (151.3, 136–167); all `/api/disruptions/*` 200 |
| `docker buildx` ARM64 image | Not built: Docker Desktop engine not running |
| UI re-check (servers had been stopped by the app) | Restarted 5183/8018. Fixed: live incident linked to a one-off mistyped key ("Deerfoot Re", 1 incident) instead of "17 Avenue & Deerfoot Trail SE" (67), now matched by parsed name then busiest within 150 m (regression test added); scroll-to-detail relied on animation frames paused in background tabs, now a post-render effect. Verified: live link, search, list/map selection, camera, prediction cascade, 14-day horizon, Predict this intersection, Reset, Guided study SUMO run (27.2%) + report; no console errors; all API calls 200/202; 23 tests pass |

## Open

- Overdispersion: replace Poisson range with negative-binomial or empirical range.
- Run the collector on a schedule (Task Scheduler/cron) to build history; not configured.
- Build/push the MCP image and create the AgentCore Runtime; add inbound auth.
- Durable dynamic data in the cloud needs a managed database behind `Store`.
- Measured CalTRACS counts still required before simulating a chosen corridor.
