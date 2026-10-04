# Validation

Run backend regression suite (real SUMO, API, MCP, chat, forecasting and SQLite/storage tests); report opt-in Timescale skips separately. Run Ruff on touched Python files and check whitespace. Verify import-boundary gate rejects application/domain dependencies on outer layers and external IO/provider SDKs. Test injected fake adapters without loading HTTP/MCP or provider implementations. No frontend change: no frontend acceptance claim.
