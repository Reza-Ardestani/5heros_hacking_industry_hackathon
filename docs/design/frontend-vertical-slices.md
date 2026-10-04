# Frontend vertical slices

The frontend previously used a generic components folder, a global types file
and a large App component holding study state, API calls and all screens.
The refactor groups code by capability:

- `features/studies`: scenario contracts/defaults, submission/polling/playback,
  flow-profile import, guided study, comparison/evidence screens and export links.
- `features/intersections`: map/list/detail/live feed, incident estimates,
  prioritization and building a study from an intersection.
- `features/forecasting`: prediction selection/evaluation, model comparison,
  benchmarks and MCP diagnostics.
- `features/assistant`: chat API, dock state and chat response contracts.
- `features/storage`: health API, refresh/abort lifecycle and storage indicator.

Each slice owns its `api.ts`, `types.ts`, UI and a public `index.ts`. Existing
study, forecast and storage tests live alongside those features. Shared code
contains the fetch transport, generic number/currency formatting and navigation/
area contracts; global CSS and existing design tokens retain their original paths.

App composes the five slices, keeps navigation/step/one-shot explorer commands
and dispatches chat actions. `useStudy` owns the study lifecycle and exposes its
controller through the studies public entry point. Study pages are separate
components within that slice. No new state or routing framework was introduced.

Intersections composes forecasting and storage through their public entry points
and consumes public study types; study state is passed through callbacks. Shared
code imports no slices. Slice code imports no application shell. Cross-slice
imports of private files are rejected, and transport calls belong in slice API
modules over shared HTTP.

`npm run architecture` checks these rules with the existing TypeScript compiler.
It runs before frontend tests/build and through root `make architecture`. A
Node test checks the real source and rejects deliberate boundary violations.
The guard covers static relative imports/exports and literal dynamic imports;
it does not prove all possible runtime dependency behavior.

Existing UI text/layout, HTTP endpoints and evidence limits remain. Screens are
feature-owned; components still use ordinary React hooks. Backend slices were
not changed by this frontend refactor.

[Requirements](../../specs/features/frontend-vertical-slices/requirements.md),
[verification](../../specs/features/frontend-vertical-slices/progress.md).
