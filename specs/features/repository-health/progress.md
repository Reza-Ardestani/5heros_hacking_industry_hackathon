# Progress

October 4: completed locally after constitution and settled four-file spec.

## Confirmed issues and corrections

- Seven journey/story links still pointed at frontend/src/components after the
  vertical-slice move. Links and labels now point to their owning feature files.
- --check --no-mcp started API/UI successfully but failed on None/mcp,
  None/mcp-info and the disabled API MCP mirror. Checks now require MCP only when
  it is enabled. Two regression tests cover disabled-service success and
  enabled-but-unreachable MCP failure.
- Full Ruff failed on four EXE001 executable modes and one I001 import block.
  Entry scripts are executable and imports organized; calculations unchanged.
- .DS_Store was untracked; metadata is now ignored without deleting the file.
- README's current warning about failing full lint replaced with accurate checks.

## Verification

- Initial make test: 77 passed, 4 skipped, then failed on five Ruff errors.
- Final make test: **79 passed, 4 skipped**, 29.12 seconds; both architecture
  guards and full backend/test/script Ruff passed. The four skipped Timescale
  tests require explicit opt-in and Docker.
- make test-web build: **14 passed**; TypeScript/Vite production build passed,
  1,613 modules, 66 CSS tokens and 21 contrast pairs. No frontend source changed.
- Actual make dev-check --no-mcp: UI/API proxy and API summary passed, exit 0.
  Flags: --no-mcp --api-port 8128 --web-port 5293 --mcp-port 8120 --quiet.
- Actual make dev-check with MCP: UI/API proxy, API summary, MCP protocol/tool
  call, self-description and API mirror passed, exit 0. Fifteen tools described;
  eleven safe self-checks passed, four unrun. Ports 8138/5303/8130.
- Smoke runs set BB_DB_BACKEND=sqlite and BB_CHAT_MODE=builtin, using separate
  ignored output/repo-health-* databases. All smoke ports closed after exit.
- **304 authored repository-relative links** resolve (immutable organizer copies,
  submission artifacts and raw research sources excluded).
- Four-file spec and git diff --check passed. No submission_artifacts diff.

## Limits

No submitted issue or submission file changes, simulator/model changes, public
messages or hosted deployment verification. Full application tests and local
startup checks do not establish field accuracy or fresh Timescale acceptance.
