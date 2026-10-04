# BB-7 — Use a qualified disruption forecast

Journey: [UJ-BB-001](../../journey.md).
Client: [ICP-BB-001](../../../Ideal_Client_Profiles/ICP_1_Planning/profile.md).

As a planner, I want to inspect expected City-reported incidents and the baseline comparison, so I can prioritize where to investigate without mistaking predictions for measured delay.

Status: **Forecast/backtest exists locally; LightGBM/auto selection is remote-branch code**. This is not new customer validation.

## Acceptance

- Target variable is City-reported incident count, not measured queue or travel time.
- History window, sparse-data behavior and flat baseline are visible.
- Candidate models and held-out evidence are reported when that branch is adopted.

Source-level evidence: [frontend/src/features/forecasting/PredictionPanel.tsx](../../../../frontend/src/features/forecasting/PredictionPanel.tsx). See owning feature progress for executed checks; source inspection is not a new runtime test.

Remote additions: [immutable branch inventory](../../../../docs/product_research/dashboard_branch_inventory.md). They have not been merged in this work.
