# Plan — proposal, not implementation evidence

1. Finalize typed measurement envelopes, source/mapping versions and two task
   readiness profiles from the [contract](../../../docs/design/data-federation/data_contract.md).
2. Add storage port and proposed local SQLite implementation: raw references,
   source/mapping versions, jobs/checkpoints, revisions, quality and version membership.
3. Implement shared read-only Socrata/Opendatasoft providers; validate pagination,
   drift, permitted query/mapping configuration and publication metadata.
4. Wire bounded qualification tools and agent policy. Select and declare actual
   LLM-assisted or deterministic policy mode; no fabricated provider calls.
5. Implement worker retry, idempotent transactional commits, restart/resume and
   reconciliation appropriate to each dataset's mutation capabilities.
6. Add coverage/freshness reports, local missing-measurement request, immutable
   data-version consumption and UI source/ingestion evidence.
7. Verify on bounded public datasets plus explicit failure fixtures; preserve
   existing simulation demonstrator. Fully qualifying an observed corridor is
   separate from onboarding its source. Do not merge unrelated cities' demand.

Suggested contribution lanes: source/semantics; ingestion/storage; qualification
agent/contracts; UI/evidence; practitioner/City-access discovery and demo. No
individual ownership assigned. Keep initial implementation to two providers and
three city catalogs. Sensor installation and new provider code generation deferred.
