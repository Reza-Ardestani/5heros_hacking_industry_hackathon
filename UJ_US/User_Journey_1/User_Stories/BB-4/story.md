# BB-4 — Observe outcome-driven revision

Journey: [UJ-BB-001](../../journey.md).
Client: [ICP-BB-001](../../../Ideal_Client_Profiles/ICP_1_Planning/profile.md).

As a engineer, I want to see the agent revise a rejected intervention after simulation, so I can judge whether the reasoning uses actual tool outcomes.

Status: **Implemented bounded policy revision; no claim that every tool is LLM-driven**. This is not new customer validation.

## Acceptance

- Trace records action, parameters, actual results, rejection reason and revision.
- Paired comparison conditions and hold-out scope stay visible.
- Failures remain failures; no synthetic success substituted.

Source-level evidence: [backend/app/application/planner.py](../../../../backend/app/application/planner.py). See owning feature progress for executed checks; source inspection is not a new runtime test.
