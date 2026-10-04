# BB-2 — Compare equivalent scenarios

Journey: [UJ-BB-001](../../journey.md).
Client: [ICP-BB-001](../../../Ideal_Client_Profiles/ICP_1_Planning/profile.md).

As a transport engineer, I want to compare baseline and alternatives on equivalent departures, so I can attribute modeled differences to the intervention.

Status: **Implemented local simulator workflow; not field validation**. This is not new customer validation.

## Acceptance

- Input hash, seed, horizon and simulator version accompany each comparison.
- Completed, unfinished and uninserted trips are accounted for; no silent teleport.
- Numerical outcomes originate in simulator outputs, not text generation.

Source-level evidence: [backend/app/application/planner.py](../../../../backend/app/application/planner.py). See owning feature progress for executed checks; source inspection is not a new runtime test.
