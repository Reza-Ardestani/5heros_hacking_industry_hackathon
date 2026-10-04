# DASH-2 — Locate a bounded study area

Journey: [UJ-BB-002](../../journey.md).
Client: [ICP-BB-002](../../../Ideal_Client_Profiles/ICP_2_Monitoring/profile.md).

As a analyst, I want to filter intersections and use a selected map area, so I can inspect a relevant shortlist.

Status: **Search/quadrant/sort local; radius-focus selector remote branch**. This is not new customer validation.

## Acceptance

- Search, quadrant and incident-count selection are source-grounded.
- Radius filter uses explicit center/distance when enabled.
- Unknown geometry and empty results do not imply absent traffic.

Source-level evidence: [frontend/src/features/intersections/IntersectionExplorer.tsx](../../../../frontend/src/features/intersections/IntersectionExplorer.tsx). See owning feature progress for executed checks; source inspection is not a new runtime test.

Remote additions: [immutable branch inventory](../../../../docs/product_research/dashboard_branch_inventory.md). They have not been merged in this work.
