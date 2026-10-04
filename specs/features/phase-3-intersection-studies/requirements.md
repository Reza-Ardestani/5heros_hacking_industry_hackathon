# S-BB-3 — Explainable decisions, intersection studies and new interventions

Requested by the user October 3, 2026, delivered in three sprints with decisions
confirmed by the user before building:

- Intersection "value in seconds" = modeled extra delay per vehicle from one typical
  lane-blocking incident there, shown with the share of "Traffic incident (unspecified)".
- New options: add/remove a signal, faster incident clearance, left-turn lane/ban.
- Selection rule unchanged (lowest delay within budget, cross-street limit, complete
  trips) but the lowest-delay option and the rule that rejected it are always shown.
- Live/intersection simulation: an intersection pre-fills the study (synthetic corridor).

Builds on [S-BB-1](../phase-1-hackathon-mvp/requirements.md) and
[S-BB-2](../phase-2-disruption-context/requirements.md).

FR-1 Each rejected option states its rule, observed value and limit; the result names
the lowest-delay option, why it lost, and the setting value that would make it eligible.
FR-2 Step 2 explains how budget, cross-street limit and demand shape the outcome and
offers one-click setting changes from the last run (inputs only; rerun required).
FR-3 Every study is stored: sim_runs, sim_actions (ordered action log), sim_alternatives,
sim_trials (seed, condition, metrics, hashes) plus a JSONL log per run in data/runs/.
FR-4 Incidents modeled in SUMO as stopped vehicles blocking 1–3 lanes at J2 for a set
duration; options evaluated in normal and incident conditions weighted by incident
frequency (intersection studies: peak lane-blocking incidents / weekday peak periods).
FR-5 New options at J2: signal ↔ priority control, clearance (shorter incident),
left-turn bay with protected phase, left-turn ban with next-junction detour penalty.
FR-6 Intersection → study: demand from 2024 volume (peak-hour and direction factors),
lanes, signal status, turn share, typical incident and weight; every assumption listed.
FR-7 Per-intersection modeled seconds of delay per incident (cached in
intersection_estimates), six-month vehicle-hours and unspecified share in the UI/list.
FR-8 Evidence summary per study: observed six-month facts + modeled effect of each option,
scaled to the observed incident count where relevant, with the proof standard stated.
FR-9 MCP tools for intersection studies, incident-delay estimates and stored runs.
TR-1 Default inputs reproduce the original four-option study and its results.
TR-2 Hold-out SUMO runs execute concurrently; results keyed by option/condition/seed.

## Acceptance

AC-1 With default inputs the step-3 banner says why First proposal (lowest delay) is not
recommended and which cross-street limit would allow it; applying it and rerunning makes
the simulator choose it.
AC-2 Database contains the run, every action, option and trial; JSONL log written.
AC-3 All new options run in real SUMO; weighted metrics equal the condition mix;
clearance changes only incident-condition results.
AC-4 Intersection study validates, cites its evidence and assumptions, runs end to end
from the Intersections tab, and returns an evidence summary.
AC-5 Seconds-per-incident estimate shown in detail and list; unspecified share shown.

Out of scope: real road geometry (OSM), measured turning counts, safety modeling of
signal changes, rerouting to parallel corridors, AWS deployment.
