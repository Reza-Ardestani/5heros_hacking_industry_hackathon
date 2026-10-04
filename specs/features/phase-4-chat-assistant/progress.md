# Progress — October 3, 2026

## Done

- Backend assistant with built-in router and optional Claude mode, both calling the MCP
  tools in-process; `/api/chat`, `/api/chat/info`.
- Chat dock UI with tool badges ("MCP · tool"), "Opened …" notes and suggestions; actions
  drive pages, intersection detail, quadrant filter, prediction panel, `mcp-info-ml` tab
  and intersection studies.
- `mcp` is now a main dependency; `anthropic` added.

## Validation evidence (Windows 11)

| Check | Result |
|---|---|
| `uv run pytest -q` | 47 passed (10 new in test_assistant.py) |
| `ruff check app tests`, `npm run build` | Passed |
| Built-in smoke, 17 questions | All routed to the expected tool and action |
| Browser, 4 actions (AC-1) | All applied; no console errors |

## Open

Claude mode untested against the live API; needs a key supplied by the user at runtime
(never committed).
