# S-BB-4 — Chat assistant over the MCP tools

Requested by the user October 3, 2026: "add a chat window on bottom of ui to ask questions
and navigate to pages as we already have mcp". Builds on
[S-BB-2](../phase-2-disruption-context/requirements.md) (MCP server) and
[S-BB-3](../phase-3-intersection-studies/requirements.md) (intersection studies).

FR-1 A chat dock at the bottom right of every page, collapsible, with suggestion chips.
FR-2 Every data answer comes from a tool on the in-process MCP server
(`app.mcp_server.build_server`), so chat, external agents and the API agree. Each reply
lists the MCP tools it used.
FR-3 Replies carry UI actions the app executes: open a page or guided step; open an
intersection; filter by quadrant; fill and run the prediction panel; open the
`mcp-info-ml` tab; build an intersection study and open guided step 2.
FR-4 Built-in mode (default) needs no key and no network: rule-based recognition of pages,
intersections (both road names), routes, quadrants, horizons, models and incident type.
FR-5 Optional Claude mode when `ANTHROPIC_API_KEY` is set (or `BB_CHAT_MODE=claude`):
Claude chooses MCP tools plus a local `navigate_ui` tool; any failure falls back to
built-in mode and says so. `BB_CHAT_MODE=builtin` forces built-in.
FR-6 Chat never writes: forecasts are not saved and `collect_latest_data` is not offered.
FR-7 Forecast answers pass on the data caveat and the held-out comparison with the flat
baseline.

AC-1 Each FR-3 action works in the browser from a typed question.
AC-2 Built-in answers match the tools' numbers (forecast in chat = prediction panel).
AC-3 Claude path: tool loop returns all tool results in one user turn, uses
`claude-opus-5-5` with server-side fallbacks, excludes write tools, falls back on error.
AC-4 No key, credential or private data in source, logs or replies.

Out of scope: streaming replies, persistent chat history, voice, running SUMO studies
from chat (the study is built; the user presses Run).
