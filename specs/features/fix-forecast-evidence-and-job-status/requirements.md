# Forecast evidence and simulation status corrections

Status: settled for implementation. User authorized both scoped fixes after independent review, October 3, 2026.

Owning stories: [BB-7 qualified forecast](../../../UJ_US/User_Journey_1/User_Stories/BB-7/story.md), [BB-4 observe revision](../../../UJ_US/User_Journey_1/User_Stories/BB-4/story.md), [BB-5 review decision](../../../UJ_US/User_Journey_1/User_Stories/BB-5/story.md).

1. Forecast summaries and assistant verdicts must use held-out scores belonging to the actual forecast model, including fallback. Automatic validation selection remains separately identified. Preserve existing `backtest` fields and model selection.
2. Add nullable `forecast_evaluation` to the shared prediction response. Missing model scores or insufficient history must be reported as unavailable; a zero-error baseline has no percentage comparison.
3. Compare and study show shared progress while submission or simulation is active, including the latest real trace. Empty state is reserved for no study. Failed jobs show failure and a recovery action. Transient polling failures retain progress and clear after recovery.
4. Preserve navigation, completed results, stale-input warning, exports and existing job polling. No database, optimizer or deployment change.
