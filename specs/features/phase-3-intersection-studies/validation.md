# Validation

- AC-1: `tests/test_simulation_log.py::test_decision_names_lowest_delay_option...`; browser
  run with defaults, apply suggested limit, rerun.
- AC-2: `tests/test_simulation_log.py::test_real_study_is_logged_to_database_and_jsonl`
  (real SUMO): runs/actions/options/20 trials/JSONL lines.
- AC-3: `tests/test_intersection_study.py::test_all_new_options_run_in_sumo...` (8 options,
  6 hold-out trials each, weighted mix exact, clearance normal == reference normal,
  turn-ban penalty, incident impact, summary).
- AC-4: `tests/test_intersection_study.py` (study derivation, weight formula, validation);
  browser: Intersections → Simulate → step 2 → run → step 3 summary + log → compare.
- AC-5: browser estimate on an uncached intersection; list row updates.
- Existing suites (S-BB-1, S-BB-2) still pass.

Not validated: realism of peak-hour/direction factors and 20-minute default incident
duration; turn shares; signal-removal safety; results on real geometry.
