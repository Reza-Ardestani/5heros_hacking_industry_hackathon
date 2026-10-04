# DASH-3 — Inspect patterns and forecast context

Journey: [UJ-BB-002](../../journey.md).
Client: [ICP-BB-002](../../../Ideal_Client_Profiles/ICP_2_Monitoring/profile.md).

As a analyst, I want to compare historical distributions with a labeled forecast, so I can form an attributable hypothesis for UJ-1.

Status: **Charts and forecast local; expanded model panel remote**. This is not new customer validation.

## Acceptance

- Counts include coverage window and source.
- Forecast is labeled modeled and links to story BB-7.
- No incident count is automatically renamed congestion or crash risk.

Source-level evidence: [frontend/src/components/PredictionPanel.tsx](../../../../frontend/src/components/PredictionPanel.tsx). See owning feature progress for executed checks; source inspection is not a new runtime test.
