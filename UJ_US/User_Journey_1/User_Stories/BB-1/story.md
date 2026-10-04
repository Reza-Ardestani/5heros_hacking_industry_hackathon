# BB-1 — Inspect sources and assumptions

Journey: [UJ-BB-001](../../journey.md).
Client: [ICP-BB-001](../../../Ideal_Client_Profiles/ICP_1_Planning/profile.md).

As a planner, I want to inspect source dates, units, methods and assumptions, so I can understand what evidence supports the proposed study.

Status: **Existing core labels; complete traffic calibration remains open**. This is not new customer validation.

## Acceptance

- Public source and retrieval time are visible.
- Observed incident facts remain separate from synthetic geometry, demand, costs and derived peak-hour factors.
- Missing measurements do not appear as zero or measured defaults.

Source-level evidence: [frontend/src/App.tsx](../../../../frontend/src/App.tsx). See owning feature progress for executed checks; source inspection is not a new runtime test.
