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

- Overdispersion: done. Negative-binomial ranges with citywide dispersion and prior_weeks=16, chosen by `scripts/evaluate_forecast.py` (3 x 28-day rolling folds, 56 slices). Citywide 80% weekly range coverage 58% -> 83%.
- Priority ranking: done. `GET /api/disruptions/priorities` and the "Where to focus next" panel (Intersections tab). Hold-out check (rank before Sep 4, score Sep 4-Oct 2): corridors 8/10 of actual top 10, Spearman 0.68; intersections Spearman 0.14, so the UI warns against ranking single intersections. Recent-change flags use a 10% FDR; none currently significant.
- Model selection: Bayes unless another model is better by >2 standard errors over 4 rolling 14-day validation windows (`scripts/evaluate_model_selection.py`, 56 slices x 3 test windows). Mean regret vs the best model 3.1% -> 2.0%; worst-model picks 69 -> 43 of 168. Glenmore Trail now Bayes (test MAE 0.87) instead of LightGBM (1.00).
- Cost & budget stress test: every run reports `cost_stress` (5x5 grid of costs and budget at -50%, -20%, 0, +20%, +50%, cost headroom, budget switch points, one-at-a-time costs, payback under costs +50% / value of time -50%), shown on the Recommendation page. Default demo: robust 25/25. Chaparral Blvd & Stoney Trail study: incident clearance holds 23/25 but has negative net value (-$4,743/yr; needs $62/h value of time), now flagged in the UI.
- Run the collector on a schedule (Task Scheduler/cron) to build history; not configured.
- Build/push the MCP image and create the AgentCore Runtime; add inbound auth.
- Durable dynamic data in the cloud needs a managed database behind `Store`.
- Measured CalTRACS counts still required before simulating a chosen corridor.

## ML forecaster (later October 3)

LightGBM (native API, Poisson objective, deterministic) added as a third model next to the
flat baseline and Bayesian rates; selection on validation days, scored on unseen test days,
UI model selector and comparison table, MCP `model` parameter. Real-data result: LightGBM
best on test for SE, NE, Stoney Trail and Deerfoot & Glenmore; worse on Deerfoot Trail and
collisions; validation picks Bayes for most slices. Tests: trend case selects LightGBM;
sparse slices fall back.

## MCP info and area focus (later October 3)

`/mcp-info` on the MCP server (catalog from the live tool list; `?check=true` runs 10 safe
tools — all ok, 60–350 ms — and lists 4 not run with reasons), mirrored at
`/api/mcp-info`. Area filter (`lat`, `lon`, `radius_m`) on intersections, predictions and
the two MCP tools; map dot click focuses 0.5/1/2 km; `mcp-info-ml` tab with per-area model
comparison, per-model forecasts, LightGBM feature importance, 11-selection benchmark
(`/api/ml/benchmark`) and MCP status. Browser-verified; 33 tests pass.
