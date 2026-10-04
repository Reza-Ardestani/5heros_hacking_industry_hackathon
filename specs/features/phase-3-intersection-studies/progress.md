# Progress — October 3, 2026

## User decisions (asked before building)

Seconds = modeled delay per incident; new options = signal add/remove, faster clearance,
turn lane/ban (redirect-to-parallel-route not selected); selection = rules +
explanation; live simulation = intersection pre-fills the synthetic-corridor study.

## Done

- Sprint 1: rejection details and decision explanation; step-2 settings advisor; step-3
  simulation log; sim_runs/sim_actions/sim_alternatives/sim_trials tables + JSONL logs.
- Sprint 2: incident blockers, J2 control, left turns, turn bay/ban in SUMO; intersection
  study builder; incident-delay estimate with cache; Intersections UI card and list
  column; "Simulate this intersection" hand-off.
- Sprint 3: four new options in the planner; normal/incident weighting from City data;
  incident impact; parallel hold-out runs; evidence summary; study design UI; MCP tools.

## Validation evidence (Windows 11)

| Check | Result |
|---|---|
| `uv run --group mcp pytest -q` | 28 passed (incl. real SUMO 8-option study) |
| `ruff check`, `ruff format --check`, `npm run build` | Passed |
| Default study regression | 196.9 / 54.0 / 143.3 / 80.7 s, revised recommended, 27.17% — identical to the recorded experiment |
| Browser, default study | Banner: "Lowest delay overall: First proposal (54s/vehicle) … cross-street delay +89% exceeds the 30% limit … would qualify with cross-street limit ≥ 90%"; Apply → 90% → rerun → simulator recommends First proposal (72.6%) with stress warning |
| Database after a study | 1 run, 14 actions, 4 options, 20 trials, JSONL log in data/runs |
| Browser, Glenmore Trail & Macleod Trail SW | +78.4 s/vehicle per incident (+363 s blocked direction), 38 veh-h/incident, 33.3% unspecified; shown in detail and list |
| Browser, Deerfoot Trail & Glenmore Trail SE | Estimate +87.2 s/vehicle, 36.4% unspecified; study pre-filled (2 lanes, priority control, 8.7% incident weight, 8 assumptions, capacity warning); 8 options run; Revised signals recommended (−6.0%); Extra lane lowest delay but over budget; clearance −1.7% overall, 19.8 veh-h saved per incident ≈ 455 over six months (modeled); 29 actions, 56 trials stored |
| Backend study, Glenmore & Macleod | Turn ban recommended (−14.4%, $10k); turn bay −47% and extra lane −62% over budget |

## Open

- Peak-hour (10%) and direction (55%) factors, 20-min incident duration and 10% turn share
  are assumptions; replace with CalTRACS counts and measured clearance times.
- Freeway interchanges exceed the arterial model (demand capped at 1,800 veh/h, warned).
- Signal add/remove is delay-only; safety effects need engineering review.
- A full intersection study takes ~2–4 min (48+ SUMO runs); progress is shown live.
