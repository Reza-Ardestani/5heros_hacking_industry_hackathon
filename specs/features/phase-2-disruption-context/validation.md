# Validation

Execute and record in progress.md:

- AC-1: monthly and category totals equal the deduplicated incident count;
  window start/end in manifest; data-gap days listed.
- AC-2: workbook sheet list; JSON manifest hashes match raw files.
- AC-3: `tests/test_disruptions.py` (summary consistency, sorted list, detail
  totals, 404, quadrant filter, offline live fallback).
- AC-4: `tests/test_forecast.py` (learned weekday pattern beats flat baseline on
  synthetic history; Poisson interval; endpoint slicing; intersection overrides
  route; horizon capped at 28).
- AC-5: real browser walk-through on the dev server with network log review.
- AC-6/7: `tests/test_disruption_store.py` (cross-feed identity, dedup to latest
  update, idempotent re-poll, partial City failure recorded, live sightings, closure
  removal, incremental archive window); real `make collect` twice with zero changes.
- AC-8: `tests/test_mcp_server.py` (10 tools, annotations, calls, saved prediction,
  error on unknown key); streamable-HTTP client probe against a running server.
- Existing S-BB-1 suite still passes (including real SUMO tests).

Not validated: forecast accuracy beyond one 28-day holdout; parser recall on
free-text descriptions beyond spot checks; closure history before retrieval; the
ARM64 image build and any AgentCore/AWS deployment.
