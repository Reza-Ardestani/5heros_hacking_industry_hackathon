# DES-BB-DATA-001 — Contract-driven data discovery and ingestion

October 3, 2026 proposal following user's request. Both offline studies and live
advice are valid consumers of one ingestion core, with different readiness gates.
Current app remains JSON snapshots and memory-only simulation jobs. This document
does not claim a DB, connector agent, live feed or integration has been implemented.

[Contract](data_contract.md), [availability research](../../product_research/data_availability.md),
[data journey](../../user_journeys/data_onboarding.md),
[architecture diagram](../../diagrams/data_pipeline.md),
[draft spec](../../../specs/features/phase-2-data-federation/requirements.md).

## Separation of responsibilities

**Discovery/qualification agent:** given city, study area, time window and task
profile, searches approved catalogs, inspects metadata/samples, identifies
measurement type, proposes a declarative field mapping, tests it, and selects
compatible sources. It can reject misleading titles, change source/allowed
mapping after validation feedback, or issue an exact missing-data report.
An LLM can assist interpretation and tool selection; deterministic checks control
promotion. A declared deterministic policy mode remains possible and must be
identified honestly. No agent provider is selected or wired in this proposal.

**Trusted ingestion core:** generic provider adapters, bounded HTTP, typed
transform registry, pagination, retries, transactional persistence, cursor
management, quality checks and immutable dataset publication. These are reusable
engineering infrastructure. Rebuilding them with an LLM on every poll adds no value.

**Simulation/decision engine:** queries qualified data versions, builds a model,
simulates permitted alternatives and returns constrained comparative evidence.
Other-city sources populate that city's namespace; they do not replace Calgary
observations by being structurally compatible.

## Bounded agent tool surface

`search_catalog`, `inspect_dataset`, `sample_records`, `propose_manifest`,
`test_mapping`, `commit_connector`, `schedule_refresh`, `read_quality_report`,
`get_coverage`, `freeze_dataset_version`, `request_missing_measurements`.
The last tool creates a local request artifact; it does not send a City message.
Tool budgets bound datasets, bytes, requests and iterations. A practical first
demo budget is three cities, two provider families, five candidates per city,
100 sample rows and at most two mapping revisions per candidate.

First providers: Socrata JSON (Calgary/Edmonton), Opendatasoft Explore v2.1
(Vancouver). They provide shared catalog/schema/record patterns; a new city on
the same family normally needs a manifest rather than bespoke Python code.
Unknown APIs, authentication schemes and PDF/Excel layouts can still require
engineering or a supported parser. Universal zero-code API onboarding is not
claimed. Documents/metadata are evidence, never executable agent instructions.

## Polling and webhooks

Start with scheduled polling. None of the probed sources was verified to provide
a subscriber webhook. Agent selects cadence from publication frequency and task
requirements: a monthly archive need not be polled like live sensors. Frequent
fetching cannot make stale observations fresh. Use conditional HTTP requests
where supported and record both retrieval and measurement age.

For a provider that documents push support, normalize its authenticated events
into the same ingestion job interface. Treat notifications as change hints,
persist/deduplicate receipt, then fetch/validate the authoritative data. Keep
periodic reconciliation for missed events. Do not build a public webhook
listener on the assumption Calgary supports it.

## Persistence and restart behavior

Proposed weekend storage: [SQLite](https://www.sqlite.org/whentouse.html) for a local single worker, behind a repository
port; PostgreSQL/PostGIS is a later option for shared workers/spatial queries.
DB choice is proposed, not added to the selected Phase 1 stack. SQLite durability
alone is not a proven multi-worker/scaled deployment architecture.

Tables: `sources`, `connector_versions`, `ingestion_jobs`, `raw_batches`,
`record_revisions`, typed normalized observations/assets/events,
`quality_results`, `dataset_versions`, `dataset_version_members`,
`simulation_runs`. Large raw payloads can be content-addressed local files with
DB references; retain exact raw bytes and hashes for replay. This differs from
the research probe's extracted summaries, which are not raw batch archives.

A transaction stores normalized revisions, quality results and the next
checkpoint only after the fetched page is durably retained. Unique source/key/
revision identities make repeated delivery idempotent. A crash before commit
replays the page; a crash after commit resumes from the recorded checkpoint.
Immutable version membership pins exact revisions consumed by each simulation.
Refreshing a source must not silently change a prior run's data.

For mutable datasets, ingestion must observe update times or revisions, not only
new event start times. Use an overlap window plus stable tie-breaking key when
update semantics are known; otherwise bounded snapshot reconciliation. Offset
pagination and an order clause alone do not provide a consistent snapshot during
concurrent publisher edits. Detect/reconcile changed records and deletions when
provider semantics allow it; report unsupported deletion detection explicitly.

## Failure classification

Timeouts, 429 and temporary server failures: bounded exponential backoff with
jitter, honor Retry-After, preserve checkpoint; exhaustion leaves a persisted
retryable failure. No retry loop makes a 401 authorized or a schema mismatch valid.
Unexpected fields/types/units: quarantine affected batch, compare schema and
ask the qualification agent for an allowed mapping revision. Ambiguous semantic
changes fail closed for decision use; raw data can remain archived. Zero counts
are valid possibilities, not automatically missing values. Quality checks flag
unexpected zero runs, duplicate conflicts, missing bins and impossible ranges.

Agent autonomy is visible in the repair decision and evidence, not in hidden
retry plumbing: discover, test, fail with a specific reason, revise/select another
source, retest, then publish or report missing measurements.

## Judge demonstration

Give the agent a city and contract profile without dataset-specific UI input.
Show discovery and evidence-based rejection: daily volume is not peak demand;
Vancouver catalog links are not count rows; selected Edmonton detector counts
are not full traffic volumes. Show conditional Calgary count mapping with unknown
semantics preserved. Once a qualified source is available, ingest to storage,
repeat the job with no duplicate normalized revisions, restart, then freeze a
dataset version for simulation. Change the profile to live advice: reject the
monthly archive on freshness and generate a targeted data-access request.

Use an explicitly labeled test fixture for transient failure/schema-drift demos;
do not imply the City API actually failed that way. The complete demo above is
planned acceptance, not today's runtime evidence. A useful autonomous output can
be “insufficient data for this decision,” with exact missing fields and next action.
