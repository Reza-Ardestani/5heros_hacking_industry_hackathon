# Validation

Run frontend Vitest suite and TypeScript/Vite production build. Exercise existing
job submission, polling disconnect/recovery, failure/completion and stale-input
UI tests; forecast-model evidence tests; storage health/cleanup tests. Add a
boundary guard that rejects shared-to-feature imports, slice-to-app imports and
private cross-slice imports. Verify the guard rejects deliberate violations.
Check authored whitespace and exactly four owning spec files. Record current
results; do not infer browser, deployment or backend acceptance from these checks.
