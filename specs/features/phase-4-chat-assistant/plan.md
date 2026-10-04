# Plan

1. `backend/app/application/assistant.py`: `Assistant` with in-process MCP calls,
   entity index (intersections, routes; cached by database version), built-in router,
   Claude tool loop (`client.beta.messages.create`, adaptive thinking, `fallbacks="default"`
   with beta `server-side-fallback-2026-07-01`), `navigate_ui` tool, `chat_mode()`.
2. `backend/app/api.py`: `POST /api/chat` {message, history} and `GET /api/chat/info`.
3. Dependencies: `mcp` moves from the optional group to main (the API now uses it; Cloud
   Run installs main only); `anthropic` added (inert without a key). The empty `mcp` group
   stays so existing `--group mcp` commands keep working.
4. Frontend: `components/ChatDock.tsx`; `ChatAction`, `ChatReply`, `ExplorerCommand`
   types; `App.tsx` executes actions; `IntersectionExplorer` takes a `command` prop
   (nonce) to filter, focus, switch tab or set the prediction selection.
5. Tests `backend/tests/test_assistant.py`; docs (README, design, constitution).

Commands: `cd backend && uv run pytest -q`, `uv run ruff check app tests`,
`cd frontend && npm run build`.
