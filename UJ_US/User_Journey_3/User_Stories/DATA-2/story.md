# DATA-2 — Ingest reliably and recover

Journey: [UJ-BB-003](../../journey.md).
Client: [ICP-BB-003](../../../Ideal_Client_Profiles/ICP_3_Data_Operations/profile.md).

As a data steward, I want to poll supported APIs through a durable ingestion core, so I can retain evidence despite transient failures and duplicate retries.

Status: **City collector exists; general resource-source ingestion proposed**. This is not new customer validation.

## Acceptance

- Timeout/retry/backoff and provider limits are explicit.
- Stable keys, revisions and checkpoints prevent duplicate replay.
- Supported webhooks use the same validation path; polling remains an option.
- Raw observations and deterministic derived fields remain distinct.

Source-level evidence: [backend/app/infra/disruption_store.py](../../../../backend/app/infra/disruption_store.py). See owning feature progress for executed checks; source inspection is not a new runtime test.
