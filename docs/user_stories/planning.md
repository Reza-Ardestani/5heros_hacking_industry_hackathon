# US-BB-001 — Auditable corridor comparison

Journeys: [UJ-BB-001 engineer](../user_journeys/planner.md),
[UJ-BB-002 reviewer](../user_journeys/budget_reviewer.md).
Client/job: [ICP v0](../product_research/ideal_client_profile.md).
Contract: [S-BB-1](../../specs/features/phase-1-hackathon-mvp/requirements.md).

Status means implemented in the local prototype, not customer-validated or
production accepted. October 3 source inspection maps the stories below to
actual code and [recorded output](../demo/example_result.json). Existing automated/
browser validation is recorded in [spec progress](../../specs/features/phase-1-hackathon-mvp/progress.md).
No new runtime acceptance is implied by this documentation update.

## Implemented stories

### BB-1 — Inspect provenance before trusting an effect

As an engineer or reviewer, I want source versions and assumptions visible so
I can distinguish observed context from model inputs.

Acceptance: incident attribution, demand kind/source, synthetic network/reference,
cost assumptions and missing calibration are inspectable. Export preserves
scenario and source context. Evidence: [incidents adapter](../../backend/app/infra/incidents.py),
[report API](../../backend/app/api.py), [UI](../../frontend/src/App.tsx).
Limit: incidents do not rank corridors or drive simulated demand; metadata
inspection does not verify a user's claimed measured source.

### BB-2 — Compare equivalent modeled traffic

As an engineer, I want alternatives evaluated on the same departure manifest
within each seed so an input change cannot masquerade as improvement.

Acceptance: named reference, engine version, seed/horizon and departure hashes
recorded; completed/unfinished/uninserted trips accounted; actual SUMO outcomes;
no teleport or silent engine success. Evidence: [simulator](../../backend/app/infra/simulation.py),
[real simulation test](../../backend/tests/test_simulation.py), recorded report.
Limit: synthetic routing/geometry; evaluation seeds select the option and are
not an independent confirmation of the selected effect.

### BB-3 — Respect budget and protected service

As an engineer or program reviewer, I want unaffordable or service-violating
alternatives excluded so the fastest modeled option does not win by default.

Acceptance: editable capital budget/cross-mean-delay guardrail; explicit rejection
reasons; censored comparisons rejected; feasible reference fallback and feasible
cost-delay Pareto options. Evidence: [evaluation](../../backend/app/domain/evaluation.py),
[domain tests](../../backend/tests/test_domain.py), recommendation UI.
Limit: aggregate cross delay is not a safety, accessibility, or equity guarantee.

### BB-4 — Inspect a real proposal/revision loop

As an engineer, I want the workflow to rescore a revised signal split from
simulator outcomes so I can inspect its rationale and changed parameters.

Acceptance: chronological proposal, simulation, scoring and revision events;
frozen alternatives evaluated on three additional seeds; selected plan compared
with reference under ±20% arrival demand. Evidence: [planner](../../backend/app/application/planner.py),
recorded trace, simulation UI. Limit: deterministic bounded policy, no trained
RL/LLM; stress failures are reported but do not filter selection automatically.

### BB-5 — Hand off a cost-aware evidence package

As a budget reviewer, I want costs, tradeoffs, rejection reasons and assumptions
exported together so I can question a recommendation without reconstructing it.

Acceptance: cost-delay frontier, editable economic assumptions, illustrative
annualization, JSON containing trace/scenario/metrics/sources/limitations; export
requires a completed job. Evidence: report API, UI, domain economic-unit test.
Limit: assumed costs and undiscounted time-value estimate, not a scoped estimate,
formal business case, lifecycle portfolio analysis, PDF report or approval.

### BB-6 — Reproduce the demonstrator (team enabling story)

As a contributor, I want separate API/UI modules and locked dependencies so I
can reproduce and extend the prototype within clear ownership boundaries.

Acceptance: documented launch/check commands, domain/application/infrastructure
separation, dependency locks and contribution lanes. Evidence: [README](../../README.md),
[contributing guide](../../CONTRIBUTING.md), tests and frontend build evidence.
Limit: verified development platform only; no hosted acceptance or durable jobs.

### BB-7 — Import a declared directional arrival profile

As an engineer, I want a sourced interval profile checked for units and coverage
so I can replace default arrivals without concealing their origin.

Acceptance: measured declaration requires citation/profile; contiguous ordered
intervals cover the duration; bounds/nonfinite values rejected; weighted rates
shown. Evidence: [scenario contract](../../backend/app/domain/models.py), domain
tests, UI import and [format](../../data/README.md).
Limit: user-normalized two-rate JSON; not automatic CalTRACS extraction, full
direction/movement mapping, verified measurements or model calibration.

### BB-8 — Recover without misreading old evidence

As an engineer, I want changed inputs, invalid data and execution failure clear
so I do not present an old or failed run as a new successful recommendation.

Acceptance: guided steps; stale-result notice after input edits; validation/error
messages; active worker conflicts; unknown/expired jobs and failed engine runs
explicit. Evidence: UI, [jobs](../../backend/app/application/jobs.py),
[HTTP/job tests](../../backend/tests/test_api_and_jobs.py).
Limit: one active job, eight retained jobs, memory-only history; no cancel/restart
recovery, accounts or multi-user review.

## Proposed next stories — not implemented or approved scope

- **F-BB-1:** Reproduce a real corridor baseline from observed geometry, timings,
  movements and counts; qualify against independent observations under engineer-
  agreed tolerances. Requires new design/spec before implementation.
- **F-BB-2:** Review a calibrated shortlist with pedestrian/transit/movement-specific
  constraints and scoped cost estimates. Current aggregate guardrail is insufficient.
- **F-BB-3:** Compare task completion and correction effort with a practitioner's
  existing study workflow. Requires consented pilot evidence; no savings claim today.
- **F-BB-4:** As an analyst, specify city/task and let the agent discover, test and
  qualify source mappings with exact coverage/semantic gaps, rather than code a
  city-specific integration. Proposed [data journey](../user_journeys/data_onboarding.md).
- **F-BB-5:** As an analyst, refresh sources into durable revisioned storage with
  bounded retry, deduplication and restart recovery, then pin a data version for
  simulation. Proposed [data design](../design/data-federation/design.md).
- **F-BB-6:** As an analyst, distinguish historical-study from live-advice readiness
  and receive a precise missing-measurement request when data is unsuitable.
  Proposed [contract](../design/data-federation/data_contract.md),
  [draft spec](../../specs/features/phase-2-data-federation/requirements.md).

Maintenance funding optimization, citywide ranking and real-time signal control
are not existing user stories. Validate the job before expanding the action space.
