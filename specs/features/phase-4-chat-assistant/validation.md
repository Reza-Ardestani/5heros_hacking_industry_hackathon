# Validation

- AC-1: browser (web 5183 / api 8018): "Top 5 hotspots in SE" → Intersections, quadrant
  SE, detail Deerfoot Trail & Glenmore Trail SE; "forecast 16th avenue NE next 14 days
  with lightgbm" → panel NE / 16 Avenue NE / 14 days / lightgbm; "Simulate Glenmore Trail
  & Macleod Trail" → step 2 with study banner; "go to evidence" → Evidence & sources.
- AC-2: chat said 10.3 incidents for 16 Avenue NE; prediction panel showed 10.3.
- AC-3: `tests/test_assistant.py::test_claude_mode_runs_mcp_tools_and_navigates` and
  `::test_claude_failure_falls_back_to_builtin` (scripted fake client, no network).
- FR-4/FR-6/FR-7: `tests/test_assistant.py` built-in tests (navigation without tools,
  hotspots, named intersection, forecast never saves and carries caveat, study action,
  help fallback, endpoint and 422 on empty message, mode selection).

Not validated: Claude mode against the live API (no key used in this build); answer
quality on free-form questions outside the built-in patterns.
