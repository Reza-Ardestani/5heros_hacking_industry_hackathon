# S-BB-DATA-1 — Source qualification and durable ingestion

Status: draft proposal responding to October 3 user request; not implemented or
claimed accepted. User confirmed historical planning and live advice are both
valid. [UJ-BB-003](../../../docs/user_journeys/data_onboarding.md),
[US-BB-001 F-BB-4–6](../../../docs/user_stories/planning.md),
[DES-BB-DATA-001](../../../docs/design/data-federation/design.md),
[contract](../../../docs/design/data-federation/data_contract.md).

FR-1 Given city, location/time scope and task profile, discover public candidate
datasets through bounded catalogs/metadata/samples; preserve evidence.
FR-2 Emit compatibility/readiness with supported measurement semantics, coverage,
units, freshness and precise gaps. Daily averages and detection subsets cannot
be silently converted into complete observed peak demand.
FR-3 Agent proposes/revises typed manifests using shared Socrata/Opendatasoft
adapters and allowed transformations. Unknown semantics remain conditional;
unsupported provider/format does not become a fabricated successful connector.
FR-4 Core schedules fetches, performs bounded retry/reconciliation, persists raw
payloads and normalized revisions, advances checkpoint transactionally, and resumes.
FR-5 Preserve updates/deletions according to provider capabilities; use idempotent
revision keys, overlap/reconciliation and schema-drift quarantine.
FR-6 Both historical and live consumers use the same contract/storage with
different readiness gates. Stale or incomplete live evidence withholds live advice.
FR-7 Freeze exact dataset revisions for reproducible simulations; keep city/local
network identities separate. Existing model calibration requirements remain.
FR-8 Surface autonomous actions, selection/rejection, mapping test results,
ingestion quality, freshness and missing-data requests in an evidence view.

TR-1 Separate domain contracts, qualification application, provider infrastructure
and storage port. Proposed local SQLite single-worker repository; deployment DB
and agent/LLM provider choices remain proposals until implementation is settled.
TR-2 Bounded public domains/requests/bytes/jobs, declarative mappings and parameterized
storage operations; no arbitrary generated code/SQL execution.
TR-3 Subscriber webhooks only for providers with verified support; polling is the
first transport. Notifications feed the same persisted ingestion job path.

Acceptance: actual source discovery/rejection, storage/replay/restart and immutable
version checks in [validation](validation.md). No new sensors, City messages,
credential procurement, field signal control, universal API onboarding, full
PDF/Excel parser, or calibrated City-effect claim in this slice.
