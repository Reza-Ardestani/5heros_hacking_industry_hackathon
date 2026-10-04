# UJ-BB-003 — External APIs and Resource Evidence

Target client: [ICP-BB-003](../Ideal_Client_Profiles/ICP_3_Data_Operations/profile.md).
Actor: transport data steward / integration analyst. Contributors: procurement,
public-works scheduling, estimators and equipment coordinators. Engineering approval
and supplier commitments remain with authorized people. [Stories](User_Stories/README.md).

Trigger: UJ-1 needs reliable traffic or cost/resource evidence for a specific place
and work window, or UJ-2 needs fresh context. Outcome: a qualified frozen evidence
version, or precise missing-data reasons and a reviewable collection request.

| Stage | Product experience | Current versus proposed |
|---|---|---|
| Define need | Declare decision profile, geography, time window, freshness, units and required fields | Proposed shared task contract; local study inputs already exist |
| Discover | Agent searches supported catalogs/APIs and authorized records; records source choices | Autonomous source discovery proposed; current City connectors are developer-built |
| Qualify | Validate schema plus semantics: price vs quantity, labor hours vs headcount, stock vs equipment booking, date/location/coverage | Proposed; no public resource API verified in this work |
| Map | Emit a bounded declarative mapping, test it, expose unsupported formats | Proposed; new unsupported provider types can require engineering |
| Ingest | Reliable core polls or accepts a supported webhook; retries, deduplicates and checkpoints | City SQLite collector exists; general resource pipeline remains proposed |
| Freeze | Pin source/mapping/revision membership used by a study | Proposed general evidence snapshot; current simulator already records input evidence/hashes |
| Assess | Compare required resources against capacity available in the actual work window | Proposed; unknown or stale supply cannot silently pass |
| Repair / revise | Bounded mapping repair or alternative source; recompute eligibility and rerun | Proposed; retain past study versions, explain what changed |

Candidate evidence types: labor rates and available crew-hours by role; asphalt
unit price and deliverable quantity; equipment category/capacity and booking window;
lead times, transport/mobilization, contingencies, permits and controller access.
An aggregate market index is context, not a quote or guaranteed supply. A bulldozer
listing is not proof that the needed machine is available to this project.

Source hierarchy: authorized current scheduling/quotes first; qualified public APIs
where available; attributed manual imports where APIs are absent. City requests,
supplier messages, purchases, or new sensors are not sent/commissioned automatically.
Traffic sensors cannot establish labor or equipment availability.

Failure paths: unit/currency/window mismatch rejects mapping; retry exhaustion retains
last-good data with stale labels; unsupported format remains unsupported; unknown
resource evidence produces conditional eligibility or an abstention under the
decision policy. Do not fabricate raw columns to make an intervention appear feasible.

[Resource design](../../docs/design/resource-evidence/design.md),
[draft spec](../../specs/features/phase-4-resource-evidence/requirements.md),
[existing collector design](../../docs/design/disruption-data/design.md).
