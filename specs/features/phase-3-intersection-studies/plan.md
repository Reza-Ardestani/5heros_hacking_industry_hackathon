# Plan

Sprint 1 — explain and log
1. `domain/evaluation.py`: structured rejection details; `explain_decision`.
2. `infra/disruption_store.py`: sim_runs, sim_actions, sim_alternatives, sim_trials,
   intersection_estimates (schema v2 with in-place migration).
3. `application/simulation_log.py` (DB + JSONL), hooked into `jobs.py`.
4. UI: decision "why not" line, rejection reasons and LOWEST DELAY badge on cards,
   step-2 settings advisor, step-3 simulation log.

Sprint 2 — incident-aware simulation and intersection studies
5. `domain/models.py`: lanes, J2 control, turn share, IncidentSpec, incident weight,
   extra options and their costs, validation of inconsistent combinations.
6. `infra/simulation.py`: J2 priority/signal, left-turn routes, turn bay + protected
   phase, turn ban + detour penalty, incident blockers, per-direction metrics.
7. `application/intersection_study.py`: study builder, incident-delay estimate (cached).
8. UI: incident-delay card (seconds, six-month vehicle-hours, unspecified %), list
   column, "Simulate this intersection" → step 2 banner with assumptions.

Sprint 3 — options and evidence
9. `application/planner.py`: extra options, normal/incident conditions with weighting,
   incident impact measurement, parallel hold-out runs.
10. `application/study_summary.py` + `study_service.py`: evidence summary.
11. UI: study design controls, dynamic test plan, evidence summary panel, dynamic
    playback tabs and option cards. MCP tools added.

Commands: `make test` (backend incl. real SUMO), `cd frontend && npm run build`.
