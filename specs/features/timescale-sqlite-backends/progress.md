# Progress

2026-10-04: constitution amended; requirements, plan, validation and progress
written before implementation. User explicitly authorized implementation.

Base: main `0a0d4ab`; branch `codex/timescale-sqlite-backends`. No new user journey,
client profile or story created; this storage spec links existing DATA-2/DASH-1.

## Implemented

- Original SQLite Store preserved as `sqlite_store.py`; facade selects SQLite by
  default or Timescale reads when its mirror is synchronized.
- Atomic local triggers, full-row recovery log, existing-data baseline, source
  UUID and ordered remote checkpoint. REAL transfer preserves double precision.
- psycopg adapter, real `travel_time_samples` Timescale hypertable, compatibility
  views, bounded timeouts/backoff and automatic destination reinitialization.
- Local writes during outages, idempotent replay, source isolation, sanitized
  status through API/MCP and visible frontend storage state.
- Version-pinned Compose service with healthcheck/named volume, ignored environment
  template, offline sync CLI, consistent API/collector dependency runtime and
  [operating guide](../../../docs/ops/storage.md). Local environment files excluded
  from Docker build contexts as well as Git.

## Verified October 4, 2026

- `BB_TEST_TIMESCALE=1 uv run pytest -q`: **78 passed**, 43.70 seconds. Includes the
  complete backend regression suite and four real Timescale container tests.
- After extending agent/CLI assertions, `BB_TEST_TIMESCALE=1 uv run pytest -q
  tests/test_timescale_integration.py --tb=short`: **4 passed**, 16.86 seconds.
  A real in-memory MCP client read synchronized status and identical SUMO results;
  a separate sync CLI process caught up without City downloads.
- Real container: TimescaleDB **2.23.1**, PostgreSQL **17**, macOS ARM64 Docker.
  Seeded existing six-month exports; matched incidents, closures, measurements,
  references, forecasts, estimates and complete actual SUMO action/alternative/
  trial history. Verified catalog hypertable and TIMESTAMPTZ partition type.
- Stopped Timescale, continued local reads/writes, opened a new Store offline,
  restarted database and caught up. Injected lost local acknowledgement after
  remote commit; live sightings remained exact. Replaced container with its named
  volume; data persisted. Removed only the disposable destination schema; the
  already-running adapter reinitialized/replayed retained history.
- Real constrained batch failure rolled back both rows and checkpoint; removing
  the test constraint permitted recovery. Four writer threads plus three separate
  Python processes shared one SQLite file and converged to 24 sightings. A second
  independent source could not pollute the mirror. Atomic local rollback, precise
  floats/nulls, read-error fallback, retry timing and credential redaction covered.
- Frontend `npm test -- --run`: **12 passed**. `npm run build`: passed, including
  TypeScript and 66 generated tokens/21 contrast pairs.
- Ruff on application, both new test modules and sync CLI: passed.
- `git diff --check`: passed. Thirteen owning Markdown files had valid local
  links; owning spec contains exactly four files. Compose `config --quiet`: passed.
- Test containers and volumes removed; pre-existing `autoheal` left untouched.

## Limits and outstanding work

- Full `uv run ruff check app tests ../scripts` reports four existing EXE001
  errors: non-executable shebang files `dev.py`, `evaluate_forecast.py`,
  `evaluate_model_selection.py`, `mcp_client_demo.py`. Their unchanged Git modes
  are outside this storage change; scoped lint is clean.
- Default mode remains SQLite. No production `.env.timescale`, database service,
  deployment or public-demo migration created. Local development services verified
  below; user subsequently authorized committing the changes to local `main`.
- Single persistent SQLite authority; both storage directories must survive
  replacement. Independent ephemeral/multi-host replicas unsupported. Retained
  recovery history grows; compaction and loss of SQLite itself remain future work.
- Typed time-series storage is implemented; no claim of faster analytical queries,
  calibrated Calgary simulation or automatic infrastructure improvement.

## Live local verification, October 4

At the user's request, restarted the API (8008, Uvicorn reload) and React/Vite
(5173, hot reload), started HTTP MCP (8000) and a persistent local Timescale service.
Generated local `.env.timescale` with private permissions and verified Git ignores
it. This is local development, not public deployment.

The initial immediate sync raced database startup. `make db-up` now waits for its
healthcheck before returning; the revised command was run successfully. Local
Framework Python lacked usable default CA certificates for Calgary HTTPS. Pointed
the ignored local environment's `SSL_CERT_FILE` at the installed certifi CA bundle,
restarted API/MCP, then verified real City requests returned 200 without disabling
certificate validation. Live feed returned one incident and 180 active closures.

Live UI/API/MCP check passed: frontend HTML/API proxy, database summary, MCP
initialize/list/predict over HTTP (15 tools), self-check (11 safe tools passed,
four intentionally not run), and reachable API MCP mirror.

Browser checks: forced LightGBM displayed its own model label, MAE and verdict;
guided study submitted a real SUMO job; Compare displayed running status, then
recommended revised signals. Run `129aa67f305a4b0797e38e697a6eff67` completed with
20 trials, 15 recorded actions, four alternatives and a working report export.
The modeled reduction was 27.2%, with synthetic corridor/default arrivals.

Stopped only this local Timescale service. API through the Vite proxy served
SQLite, saved a new forecast, exposed queued changes and retained the completed
study. An independent process read that study during the outage. Browser showed
SQLite recovery. Restarted Timescale with its existing volume, drained changes;
the live API recovered automatically after bounded retry backoff, reported zero
queued changes, retained the forecast and all trials. No new browser console
errors appeared after the restart settled. Old transient Vite errors occurred
during stopping/restarting its process.

All four local services left running. Screenshots saved locally at
`/tmp/bb-live-recommendation.png`, `/tmp/bb-live-sqlite-fallback.png` and
`/tmp/bb-live-timescale.png`. No commit, push or public demo change.

## Delivery authorization, October 4

After live validation, user requested committing to `main`. Delivery scope is the
local commit and merge into `main`; remote push and deployment are not requested.
Private environment, database files and generated run logs remain ignored.
