# Contributing

Read [AGENTS.md](AGENTS.md), the constitution, organizer sources, and the owning
four-file feature spec. The Phase 1 contract is settled for this early prototype;
organizer acceptance is a separate gate. Keep journeys, stories, designs and
specs in their homes; link through docs/modeling.md. Record scope changes before
implementation, with honest completed/open evidence.

## Five parallel ownership lanes

Choose owners together; the following are roles, not assignments to named members.

| Owner | Scope | Deliverable |
|---|---|---|
| Data/calibration | data/, scripts/, source licenses | One cited CalTRACS study; units and movement mapping |
| Simulation | backend/app/infra/simulation.py | Inspected network/signals; baseline queue/travel-time checks |
| Decision engine/API | domain/, application/, api.py | Constraints, paired evaluation, honest failure/report behavior |
| Frontend | frontend/ | Real API integration, playback, accessible input/error/results |
| Product/demo | docs/, organizer_docs/, submission preparation | User validation, cost assumptions, pitch, sources and approval evidence |

Agree the Scenario/result contract before changing shared fields. Keep domain code
HTTP-independent; orchestration in application; external IO in infra; UI separate.
One backend is enough now. Extra services require a concrete need and a new design
boundary. Use small branches and reviewable pull requests; include validation and
model limitations. Do not push to the organizer repository's main branch.

## Definition of done

- Behavior matches the owning spec; source provenance and units are explicit.
- Run `make test` for backend changes and `make build` for frontend changes.
- For end-to-end behavior, run the browser experiment and exported report.
- Compare identical input manifests, account for every planned trip; reject censored
  comparisons. A failed simulator or unavailable dataset never becomes fabricated output.
- Update feature progress with commands, results, limitations and remaining gates.
- Preserve organizer originals, exclude raw participant excerpts/secrets/generated caches.

Tests should challenge boundaries or real behavior, not mirror implementation.
Do not prefill results, infer flow from incident frequency or label generated OSM
signals as observed. Freeze proposals before evaluation; report per-seed variability.
Record an authentic fallback when no alternative is feasible. No trained-model,
City endorsement, field benefit, registration or submission claim without evidence.

## Weekend priorities

First secure organizer validation and one usable counted corridor. Next inspect
network and baseline against measured queues/travel times. Then rerun paired
alternatives and sensitivity. Keep working synthetic demo as fallback, labeled.
Reserve time for a recorded demo, 2–5 screenshots, design package and submission.
RL training and broad city optimization are outside the weekend prototype.
