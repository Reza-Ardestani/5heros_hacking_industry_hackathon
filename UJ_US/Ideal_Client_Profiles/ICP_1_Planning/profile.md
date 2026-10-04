# ICP-BB-001 — Intervention and prediction client

Status: proposed, October 3, 2026. No customer interviews, purchase intent, or
City partnership established. This profile is adapted from the architecture-branch research, not a new interview.
Journey: [UJ-BB-001](../../User_Journey_1/journey.md).

## Primary user and job

A municipal transportation engineer or consultant study lead responsible for a
bounded, signalized corridor study. They have engineering expertise and need to
compare permitted interventions, preserve service constraints, and explain a
recommendation before a planning or budget review.

Job: **When asked whether to retime a corridor or consider added capacity, help
me produce a reproducible comparison with explicit costs and rejected options,
so a reviewer can judge the next study or pilot without losing the assumptions.**

This is a proposed target job. Current prototype supports a synthetic version;
it cannot yet ingest and reproduce a complete professional corridor model.

## Buying and review roles — hypotheses

| Role | Proposed responsibility | Validation needed |
|---|---|---|
| Daily user/champion | Transportation engineer or consultant analyst; prepares comparisons | Exact workflow, repetition and missing handoffs |
| Technical approver | Qualified engineering lead; judges model validity and constraints | Required calibration, model formats and review standards |
| Decision reviewer | Mobility program manager/budget analyst; reviews tradeoffs | Accepted evidence, decision authority and other objectives |
| Economic buyer | Municipal program owner or consulting practice principal | Budget ownership, purchasing route, procurement requirements |
| Beneficiaries | Travelers and affected communities | Multimodal impacts and local priorities; motorists are not the software buyer |

These are role hypotheses, not confirmed Calgary titles or purchasing authority.
Council/project approval processes remain outside the application.

## First pilot fit

Seek a team with a completed or active corridor study, permission to share its
model/observations, an engineer available to review outputs, repeated alternative
evaluations, and a defined deliverable deadline. A transportation consultancy
may offer a practical pilot route; that access advantage remains unverified.
Calgary is the geographic research anchor, not a claimed customer.

Disqualify an initial pilot if no suitable measurements/model can be shared,
the real pain is pavement/bridge renewal prioritization, existing automation
already meets the need, or the buyer only wants direct real-time signal control.
Province-wide investment, emergency operations and consumer route navigation
are outside this first use case.

## Pains to validate

| Proposed pain | Evidence we would accept | Current support |
|---|---|---|
| Repeated preparation/reruns consume scarce analyst time | Recent study artifacts; measured task time and correction effort | Prototype automates its fixed scenario; customer workload unmeasured |
| Reviewers cannot trace why options were rejected | Actual review questions, handoff failures or revision history | Budget/guardrail rejection and trace implemented locally |
| Cost assumptions become detached from simulated results | Real estimate/report mismatch or repeated reconciliation | Editable assumed costs exported with the scenario |
| Averages hide who gets worse service | Practitioner's required per-movement/mode metrics | Main/cross aggregate delay only; richer protections absent |

## Proposed value and commercial test

Start with a supervised study pilot that complements the customer's existing
tools. Compare time to a correct, reviewable deliverable on the same case.
Include setup, source transformation, engineering corrections and report review;
simulation runtime alone is not the productivity metric.

Measure analyst/reviewer hours, unsupported claims, evidence traceability, and
agreement with the accepted baseline. Define tolerances with the engineer before
evaluation. Pricing per study or per team remains an experiment; no market size,
revenue, savings percentage or procurement shortcut is claimed.

## Resource-aware decision extension

The engineer also needs a dated cost/resource envelope for each alternative: labor,
materials, equipment, location, and work window. Budget reviewers need the source
and confidence of those inputs. Procurement or public-works staff may supply them;
they are collaborators rather than the assumed daily user. Lack of construction
resources does not establish that signal retiming is technically safe or available.
