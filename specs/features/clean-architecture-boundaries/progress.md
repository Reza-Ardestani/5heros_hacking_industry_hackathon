# Progress

October 4: completed locally; developed on `codex/clean-architecture`.

## Changes

- Application-owned persistence, simulator, City fetch/raw sink, neutral tool and
  chat model ports; shared API/MCP/CLI composition in `app/bootstrap.py`.
- Disruption services receive storage/network dependencies. Collector receives
  fetcher and optional raw sink. Source attribution moved to a pure catalog.
- Offline export seeding, simulation log files, MCP result normalization, Claude
  SDK and LightGBM implementation live in infrastructure. Existing numerical
  implementation, model parameters, HTTP/MCP fields and database schemas retained.
- Assistant uses dictionary tool/model responses; provider SDK objects stay outside
  application. Existing chat write restrictions and fallback behavior remain tested.
- `make architecture` guards inner imports and direct filesystem IO, also runs
  before `make test`. New tests exercise isolated inner imports and injected tools/models.

## Verification

- `cd backend && uv run pytest -q`: **77 passed, 4 skipped**, 25.05 seconds. Covers
  real SUMO, domain rules, forecast selection/evidence, HTTP, MCP, chat, collector,
  SQLite and mocked storage faults. Four skipped tests require opt-in disposable
  Timescale containers; no fresh real Timescale outage/recovery acceptance claimed.
- `make architecture`: passed. Fresh-process inner-module import test loads no
  infrastructure, API, MCP adapter, bootstrap or external provider SDKs.
- Ruff on backend app/tests, architecture checker and collector/build CLIs: passed.
  Evaluation scripts pass with only pre-existing EXE001 ignored. Full repository
  lint still reports four existing shebang/executable-mode errors in dev.py,
  evaluate_forecast.py, evaluate_model_selection.py and mcp_client_demo.py.
- Collector and dataset build `--help` entry points: passed, without collection.
- `git diff --check`: passed.

## Limits

Pydantic domain contracts, process-local forecast registration/caches and threaded
jobs remain intentional speed tradeoffs. The static gate does not prove every
possible dynamic dependency. Frontend unchanged; no frontend/device/provider or
deployment acceptance claimed. No public submission performed.
