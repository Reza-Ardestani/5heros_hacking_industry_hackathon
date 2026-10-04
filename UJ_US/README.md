# User journeys, stories, and client profiles

Canonical home selected by the user October 3, 2026. Each journey has its own
folder and Markdown file; each corresponding story has its own folder and file.
Profiles have their own supporting folders. Designs, diagrams, and four-file
implementation specs remain separate; [modeling catalog](../docs/modeling.md).

| Journey | Target user / supporting profile | Story index | Delivery boundary |
|---|---|---|---|
| [UJ-BB-001 — Intervention and Prediction](User_Journey_1/journey.md) | [ICP-BB-001](Ideal_Client_Profiles/ICP_1_Planning/profile.md): municipal transport engineer / consultant analyst, engineering lead and budget reviewer | [Stories](User_Journey_1/User_Stories/README.md) | Simulation/revision/report exist; real-world calibration and resource constraints remain open |
| [UJ-BB-002 — Dashboards](User_Journey_2/journey.md) | [ICP-BB-002](Ideal_Client_Profiles/ICP_2_Monitoring/profile.md): mobility analyst / operational reviewer | [Stories](User_Journey_2/User_Stories/README.md) | Local intersection dashboard exists; newer remote branch features identified separately |
| [UJ-BB-003 — External APIs and Resource Evidence](User_Journey_3/journey.md) | [ICP-BB-003](Ideal_Client_Profiles/ICP_3_Data_Operations/profile.md): transport data steward with procurement/public-works collaborators | [Stories](User_Journey_3/User_Stories/README.md) | City collector/MCP exist; autonomous provider onboarding and labor/material/equipment evidence are proposed |

Read a profile, then its journey, then its story folder. Status means source-level
implementation evidence or a proposed requirement; it does not mean a customer
validated the workflow or that every branch was executed in this review.

Related: [branch feature inventory](../docs/product_research/dashboard_branch_inventory.md),
[resource evidence design](../docs/design/resource-evidence/design.md),
[draft resource spec](../specs/features/phase-4-resource-evidence/requirements.md).
Legacy `docs/user_journeys/planner.md` and `docs/user_stories/planning.md` redirect
here to preserve existing links without maintaining duplicate canonical content.

Names use “Intervention and Prediction,” the user's final wording. “Prevention”
is an intended outcome to investigate, not a current promise of preventing incidents.
