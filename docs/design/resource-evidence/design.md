# DES-BB-RESOURCE-001 — Resource-aware intervention feasibility

Status: proposed design, user requested October 3. No workforce, materials,
equipment or supplier integration implemented by this documentation work.
[UJ-BB-001](../../../UJ_US/User_Journey_1/journey.md),
[UJ-BB-003](../../../UJ_US/User_Journey_3/journey.md),
[BB-8](../../../UJ_US/User_Journey_1/User_Stories/BB-8/story.md),
[draft spec](../../../specs/features/phase-4-resource-evidence/requirements.md).

## Decision rule

Compare like-for-like modeled delay, cost and distributional effects only after
assessing eligibility. The current simulator uses vehicle delay; person delay
requires occupancy/mode measurements and must not be relabeled as observed.
Cost remains explicit, with budget limits and a cost-delay frontier rather than
an unexplained mix of dollars and seconds in one score.

A physical intervention has requirements by resource category and work window.
Qualified availability is compared with those requirements in matching units,
location and time. Insufficient confirmed supply makes that option infeasible.
Unknown, stale or tentative supply makes feasibility conditional; withhold an
unconditional recommendation until the decision policy's evidence gates pass.
Do not infer lack of supply from a missing API record.

If construction cannot be supplied, the agent may assess signal retiming, incident
clearance or no change. Each retains its own technician/equipment/controller access,
service/safety and approval requirements. Retiming is not automatically cheap,
available or safe. A no-change/defer decision is valid when alternatives cannot be justified.

## Typed evidence interface — proposal

| Record | Required meaning |
|---|---|
| Envelope | Evidence ID, source/provider URI, city/location, source revision, retrieval time, observation/quote time, validity window, units, method and observed/derived/assumed status |
| Cost | Currency, unit rate and basis, applicable quantity, estimate/quote/index classification, tax/transport/mobilization scope, range and expiry |
| Labor | Role/skill, authorized crew-hours by work window, location, allocation/commitment status; hourly rate is not availability |
| Material | Material/specification, deliverable quantity/unit, location, delivery date/lead time; a price index is not a supply commitment |
| Equipment | Category/capacity, quantity, booking/work interval, location/mobilization, supplier commitment; a public listing is not a confirmed booking |
| Intervention requirement | Work activities, required quantities/hours/equipment, timing, dependencies and engineering assumption owner |
| Assessment | Feasible / infeasible / conditional, requirement-vs-supply calculations, exact gaps, policy and frozen evidence version |

Calendar alignment matters: crew availability on Monday cannot justify work planned
on Friday. Currency and unit conversion must be source-backed; contradictory
versions are quarantined. Hard resource constraints are distinct from cost estimates.
Initial scope assesses individual alternatives; allocating shared resources across
a portfolio would require additional scheduling/optimization work.

## Source and agent boundary

Public resource APIs have not been verified in this task. Start with authorized
quotes/scheduling records or attributed manual imports when APIs are unavailable.
Traffic sensors cannot measure workforce or equipment availability. Add new
measurements only when the decision has a demonstrable evidence gap.

An agent can discover supported catalogs, propose a declarative mapping, test it,
and repair within a bounded attempt budget. The trusted ingestion core owns timeouts,
rate limits, retry/backoff, pagination, deduplication, revisions, quarantine and
transactional checkpoints. Unsupported providers may need engineering. Use polling;
webhooks are conditional on actual provider support.

Preserve raw records. Deterministic derived values have an explicit transformation
version and lineage; assumptions occupy separate fields/records, not fabricated
source columns. [New organizer guidance](../../../organizer_docs/discord/updates-2026-10-03-evening.md)
rejects fictitious columns; separately labeled synthetic simulation eligibility
remains an unresolved organizer question, not a verified exception.

Freeze inputs for each decision. Updates to prices or availability create a new
snapshot and mark earlier recommendations stale; rerun and explain changes.
Do not silently rewrite past reports. External requests, bookings, purchases or
supplier/City communications require separate human authorization.
