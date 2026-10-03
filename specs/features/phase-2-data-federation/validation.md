# Validation — planned, not run

- Public integration: discover Calgary count candidate; distinguish daily totals;
  detect Vancouver report-link-only rows and Edmonton detector-count limitation.
  Archive each source/schema/measurement explanation used by the decision.
- Normalization: nonnegative finite counts, interval boundaries, units, timezone/
  daylight-saving ambiguity, location crosswalk and measured/estimated/synthetic
  labels; unresolved semantics cannot pass decision-readiness gates.
- Duplicate/revision: repeat identical page with no duplicate normalized revision;
  changed same-key row retained as new revision; preserve source precedence/version.
- Crash recovery: terminate before/after commit, restart persisted job, replay
  without losing page or advancing checkpoint prematurely.
- Retry fixtures: timeout, 429/Retry-After and server error; bounded failure and
  resume. Auth/invalid schema/mapping errors are not treated as transient success.
- Mutation/pagination: edits and deletions during fetch; explicit consistent-snapshot
  or reconciliation behavior, not reliance on offset ordering alone.
- Drift: new schema fingerprint quarantines; agent attempts permitted mapping
  revision within tool budget; ambiguous semantics remain conditional/failed.
- Two profiles: recent retrieval of old counts never passes live freshness; a
  historical study can qualify when its study/date/coverage requirements are met.
- Versioning: after source refresh, old simulation still resolves exact original
  raw/mapping/normalized revisions; cross-city IDs cannot collide.
- End-to-end: city/task request produces observable qualification/ingestion
  evidence and real stored version, or a precise missing-data outcome. No sample
  fixture is presented as an actual City response or autonomous live integration.

No tests, DB recovery proof, provider-agent execution or production acceptance
have been performed for this draft feature. Research HTTP probes are separate.
