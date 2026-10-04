# Frontend vertical slices

Status: settled. User authorized quick adoption October 4, 2026.

1. Organize frontend by studies, intersections, forecasting, assistant and storage
   capabilities, each owning its UI, API calls, response types and relevant tests.
2. Extract study state, submission/polling/playback and flow-profile import into
   the studies slice. App owns navigation and cross-feature composition only.
3. Cross-feature imports use public index.ts entry points. Shared code contains
   transport, generic formatting, navigation/area contracts and existing design tokens.
4. Preserve all routes, response contracts, UI text/layout, wizard flow, forecast
   evidence, job lifecycle/recovery, exports, chat actions and storage status.
5. Add a lightweight dependency guard; preserve backend clean architecture work.
   No new state library, endpoint/schema change, deployment or public submission.
