# Progress

October 4: completed locally after constitution and settled four-file spec.

## Changes

- README follows submission-inspired problem, journeys, architecture, dataset,
  results and future-work sections. Supplied architecture images embedded with
  relative paths; original submission files unchanged.
- SQLite default and configurable Timescale mirror explained alongside diagrams.
  Recorded result metrics checked against the existing exported report.
- README ends with prerequisites, make dev, separate make api/make web terminals,
  endpoints, checks, optional collection/storage and hosted configuration links.
- Makefile defaults to help; adds test-backend/test-web and PYTHON/DEV_ARGS
  overrides. Existing API/UI/MCP launcher and test behavior retained.

## Verification

- make help: passed. Dry-run of documented targets and custom port/Python
  overrides matched existing launch code.
- BB_DB_BACKEND=sqlite BB_CHAT_MODE=builtin
  BB_DB_PATH=output/readme-smoke/disruptions.sqlite make dev-check
  DEV_ARGS='--api-port 8118 --web-port 5283 --mcp-port 8110 --quiet': passed,
  exit 0. UI document/API proxy, backend health/summary, MCP protocol/tool call,
  MCP self-description and API mirror passed. MCP described 15 tools; safe
  self-check ran 11 successfully and left 4 unrun. All three ports closed after exit.
- 35 README local links/images/anchors resolved. Both PNGs visually inspected.
- Recorded 27.17% delay reduction, 14.80% cross-delay increase, CAD 15,000 cost,
  three completed hold-out seeds and stress success match example_result.json.
- Exactly four owning spec files verified; git diff --check passed.

## Limits

Documentation and Makefile convenience changes; no application source changes.
No fresh full-suite, browser, hosted deployment, Timescale or field acceptance
claimed. Existing full-lint executable-mode errors remain documented. Supplied
submission_artifacts was already untracked; no submission text/image modification,
commit, push or public submission performed by this change.
