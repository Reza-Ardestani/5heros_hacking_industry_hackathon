# BB-3 — Set constraints and inspect exclusions

Journey: [UJ-BB-001](../../journey.md).
Client: [ICP-BB-001](../../../Ideal_Client_Profiles/ICP_1_Planning/profile.md).

As a planner, I want to set a budget and cross-street service constraint, so I can identify options that respect study limits.

Status: **Implemented budget/service checks; labor/equipment gating is proposed**. This is not new customer validation.

## Acceptance

- Every rejected option names its rule, value and limit.
- The no-change reference remains a fallback if no eligible improvement exists.
- Changed assumptions mark old results stale until rerun.

Source-level evidence: [frontend/src/components/DecisionExplain.tsx](../../../../frontend/src/components/DecisionExplain.tsx). See owning feature progress for executed checks; source inspection is not a new runtime test.
