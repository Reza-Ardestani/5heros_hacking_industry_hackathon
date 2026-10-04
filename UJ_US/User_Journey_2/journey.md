# UJ-BB-002 — Dashboards

Target client: [ICP-BB-002](../Ideal_Client_Profiles/ICP_2_Monitoring/profile.md).
Actor: mobility analyst / operational reviewer; engineer accepts a study handoff.
Buyer: municipal program owner or consultancy lead, unvalidated.
[Stories](User_Stories/README.md). [Branch inventory](../../docs/product_research/dashboard_branch_inventory.md).

Trigger: daily review or a corridor inquiry. Outcome: a source-attributed shortlist
and bounded study handoff, not a dashboard presented as proof of an intervention.

| Stage | Existing feature in local source | Proposed addition / pain addressed |
|---|---|---|
| Orient | City-reported incidents/closures and last fetch, 60-second refresh | Separate retrieval freshness from observation coverage; a fresh fetch does not guarantee live measurements |
| Locate | Intersection search, quadrant filters, incident-count sorting, overview map | Keep a shareable bounded selection; newer radius focus is remote-branch code |
| Inspect | Historical totals, temporal distributions, incident types and nearby live context | Make unknown location/coverage and omitted records explicit |
| Compare evidence | Route/lane/category prediction with backtest against flat average | Use the same selected geography/time context; multi-model selector is remote-branch code |
| Open study | Intersection-to-study prefill and modeled incident-delay estimate | Carry versioned source selection and resource readiness into UJ-1, without treating derived peak-hour assumptions as measured flows |
| Review / return | Study evidence and persisted runs available in API/MCP | Saved dashboard view and reviewer-ready comparison/export are proposed |

The dashboard must make a decision handoff faster and more reliable; displaying
more charts is not itself the value hypothesis. Source reviewed at immutable branch
commits; no dashboard branch was merged or its new features executed in this review.

Failure paths: last-good live result keeps an error/freshness label; unsupported
geography is explicit; no matching records is not proof of no traffic; predictions
with insufficient history show the limitation. Deep links/saved views are planned,
not existing functionality.

Dependencies: raw/qualified evidence from UJ-3; intervention work in UJ-1.
[Current disruption spec](../../specs/features/phase-2-disruption-context/requirements.md).
