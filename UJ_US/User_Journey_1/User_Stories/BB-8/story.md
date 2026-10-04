# BB-8 — Exclude resource-infeasible interventions

Journey: [UJ-BB-001](../../journey.md).
Client: [ICP-BB-001](../../../Ideal_Client_Profiles/ICP_1_Planning/profile.md).

As a planner, I want to compare dated resource requirements with availability, so I can avoid recommending construction that cannot be supplied in the work window.

Status: **Proposed; no current workforce/equipment integration**. This is not new customer validation.

## Acceptance

- Missing construction capacity produces an explained rejection when evidence establishes a shortage.
- Unknown or stale capacity is conditional; never silently feasible.
- Retiming must satisfy its own technician/controller access and service/safety constraints.
- A changed resource snapshot creates a new study version; past decisions remain reproducible.

Planning links: [resource design](../../../../docs/design/resource-evidence/design.md), [draft resource spec](../../../../specs/features/phase-4-resource-evidence/requirements.md).
