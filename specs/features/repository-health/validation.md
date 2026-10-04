# Validation

- make test: backend pytest, both architecture gates and full backend/script Ruff.
- make test-web build: existing UI tests, slice guard, token contrast and production build.
- Actual make dev-check with and without MCP on separate local ports; confirm exit
  status and server shutdown. Isolate smoke database under ignored output/.
- Focused launcher tests require only API/UI when MCP is disabled and reject
  unreachable MCP when enabled.
- Check authored local links excluding immutable organizer sources and submission files.
- Ensure exactly four feature files, clean whitespace and no submission diff.
