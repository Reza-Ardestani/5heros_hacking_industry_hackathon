# S-BB-RESOURCE-1 — Resource evidence and intervention eligibility

Draft planning artifact, user authorized modeling October 3; implementation has
not started. Provider access, evidence freshness policy, requirements estimates
and engineering review criteria must be settled before coding integrations.
[UJ-BB-003](../../../UJ_US/User_Journey_3/journey.md),
[stories](../../../UJ_US/User_Journey_3/User_Stories/README.md),
[BB-8](../../../UJ_US/User_Journey_1/User_Stories/BB-8/story.md),
[design](../../../docs/design/resource-evidence/design.md).

FR-1 Qualify source semantics/units/window for traffic, costs, labor, materials and equipment.
FR-2 Keep raw observed records, derived features and assumptions separate and attributed.
FR-3 Discover and map supported providers through bounded agent tools; unsupported stays explicit.
FR-4 Shared reliable ingestion supports polling, retries, deduplication, revisions and checkpoints.
FR-5 Compare intervention requirements with available resources in the actual work window.
FR-6 Expose feasible/infeasible/conditional outcomes; unknown supply does not establish feasibility.
FR-7 Assess operational alternatives against their own constraints; retain no-change/defer fallback.
FR-8 Freeze evidence and preserve old reports; updates require new eligibility assessment and rerun.
TR-1 Domain assessments depend on typed ports, separate from HTTP, storage and provider formats.
TR-2 No generated arbitrary code, invented source values or unauthorized external side effects.

Acceptance planned: a sourced construction-capacity shortage excludes that option;
an eligible operational option or defer remains explained; stale/missing/contradictory
evidence yields conditional status; replay/restart doesn't duplicate evidence; past
decisions reproduce from pinned versions. No live provider or field-benefit claim.
