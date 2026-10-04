# Feature Specifications

Structure adapted from the live RadarCX backend constitution and its
`phase-1-1-backend-constitution-and-release-branch-alignment` precedent,
reviewed October 2, 2026. RadarCX checkout HEAD was
`9b22734d4f6a491a654cb7b4ce6ef50b49715bf5`; reference files were read from its
working tree and may include uncommitted changes. This records provenance,
not exact committed contents or inheritance of RadarCX product requirements.

Each flat feature folder contains exactly:

1. `requirements.md`: goal, requirements, acceptance criteria, scope decisions.
2. `plan.md`: implementation sequence, boundaries, and concrete commands once known.
3. `validation.md`: checks mapped to acceptance criteria and evidence requirements.
4. `progress.md`: status, completed work, validation evidence, blockers, next step.

Design narrative and diagrams are separate artifacts; link them when available.
Never copy backend phase history, completion claims, runtime commands, or user
stories into a new project as though they apply here.

[Phase 1](features/phase-1-hackathon-mvp/requirements.md) now owns the Bottleneck
Busters early implementation contract. Product/technical decisions and traceability
were settled under the user's October 3 build authorization. External organizer
acceptance and measured Calgary calibration remain separate open gates. See its
progress file for actual validation and delivery state.

[Phase 2](features/phase-2-disruption-context/requirements.md) adds the six-month
Calgary disruption dataset, intersection explorer and area/route/lane prediction.
[Phase 3](features/phase-3-intersection-studies/requirements.md) adds explainable
decisions, simulation logging, incident-aware intersection studies and new interventions.
