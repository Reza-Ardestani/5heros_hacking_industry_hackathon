# Acceptance checks

- Forced Flat and LightGBM evidence matches their own held-out rows even when automatic selection is Bayes; automatic summary remains unchanged.
- Actual fallback model determines evidence. A model eligible on full history but not backtest folds has null evidence. Insufficient history and zero-error baseline are explicit.
- Assistant reports the same model-specific percentage as the API and does not substitute automatic-selection scores.
- Compare stays informative through submission, running, poll failure/recovery, terminal failure and completion. Navigation retains the active job. Idle still shows setup guidance; updated inputs retain the completed-result warning.
- Focused backend tests, frontend UI regressions, production build and whitespace check pass. Live deployment is outside these checks.
