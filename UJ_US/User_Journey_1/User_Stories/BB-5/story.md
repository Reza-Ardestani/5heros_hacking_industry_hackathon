# BB-5 — Export a reviewable decision

Journey: [UJ-BB-001](../../journey.md).
Client: [ICP-BB-001](../../../Ideal_Client_Profiles/ICP_1_Planning/profile.md).

As a budget reviewer, I want to export the recommendation and alternatives with economic assumptions, so I can review the same evidence as the analyst.

Status: **Implemented reports and economic estimates; savings remain modeled**. This is not new customer validation.

## Acceptance

- Report contains sources, inputs, hashes, per-option results, rejection reasons and limitations.
- Cost-delay alternatives and side-road effects remain visible.
- Economic values identify currency, horizon and editable assumptions.

Source-level evidence: [frontend/src/components/DecisionExplain.tsx](../../../../frontend/src/components/DecisionExplain.tsx). See owning feature progress for executed checks; source inspection is not a new runtime test.
