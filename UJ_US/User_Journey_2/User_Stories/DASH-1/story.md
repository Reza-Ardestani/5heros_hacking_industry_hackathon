# DASH-1 — Review fresh and historical context

Journey: [UJ-BB-002](../../journey.md).
Client: [ICP-BB-002](../../../Ideal_Client_Profiles/ICP_2_Monitoring/profile.md).

As a mobility analyst, I want to review incidents, closures and coverage together, so I can understand what changed and what is currently known.

Status: **Existing local source; no new branch runtime acceptance**. This is not new customer validation.

## Acceptance

- Last fetch and provider failure are visible.
- Last-good observations remain labeled when refresh fails.
- Observation date and retrieval date are distinguishable; refresh speed does not prove source freshness.

Source-level evidence: [frontend/src/components/IntersectionExplorer.tsx](../../../../frontend/src/components/IntersectionExplorer.tsx). See owning feature progress for executed checks; source inspection is not a new runtime test.
