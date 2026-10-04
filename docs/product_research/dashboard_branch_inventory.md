# Dashboard branch inventory — October 3, 2026

Read-only Git fetch and immutable source comparison. No checkout switch, merge,
remote feature execution, deployment or updated test-result claim.

## Snapshots inspected

- `HEAD`: `7e329b26a17ee5a7d1eef529d2dbac5edd2471b3`.
- `origin/Feature/LiveDataIntersections`: `371e15b6cf95d0c31c55c1a19c0dc320b928d85e`.
- `origin/Feature/MCP_LightBGM`: `5dc1771cbce29cee7d073a642f8023b2abb11bd2`.
- `origin/feat--arch`: `1ace122490d8a2c44908c68360d6a0f2c8869ecd`.

## Features to reuse or assess

| Feature | Source boundary | Journey placement | Suggested addition |
|---|---|---|---|
| Live incident/closure context, last-good refresh, 60-second poll | Local IntersectionExplorer + live API | UJ-2 / DASH-1 | Observation freshness separate from retrieval time |
| Search, quadrant, sorting, overview map, historical patterns | Local IntersectionExplorer | UJ-2 / DASH-2/3 | Saved view and coverage/gap labels |
| Per-intersection modeled delay and open-study prefill | Local IntersectionExplorer + intersection_study | UJ-1 / UJ-2 handoff | Frozen context/resource snapshot; explicit calibration limits |
| Route/lane/category forecast, hold-out MAE vs flat average | Local PredictionPanel + forecast domain | UJ-1 / BB-7; UJ-2 display | Preserve prediction target and sparse-data limits |
| Map area/radius filtering and selectable 500/1000/2000m area | origin/Feature/MCP_LightBGM code; not adopted locally | UJ-2 / DASH-2 | Check shared selection across map, prediction and MCP |
| Auto, Bayesian, flat and LightGBM forecast selection plus model comparison | origin/Feature/MCP_LightBGM code; not executed here | UJ-1 / BB-7 | Validate chronology, leakage, sample coverage and baseline comparison before adoption |
| MCP self-description/model info panel | origin/Feature/MCP_LightBGM code | UJ-3 operator diagnostics; optional demo detail | Keep technical diagnostics out of the planner's main decision path |
| One-command UI/API/MCP local launcher | origin/Feature/MCP_LightBGM source | Technical enablement / BB-6 | Verify dependencies and launch behavior before documenting acceptance |

Files reviewed include frontend/src/components/{IntersectionExplorer,PredictionPanel}.tsx,
backend/app/api.py, remote diffs and source snippets, and the remote research profile.
The local branch is behind the fetched remote; this inventory does not imply that
all newer code is running. Branch feature ownership can change; commits above pin
this assessment. Source implementation does not establish external data validity.

The architecture-branch ICP-BB-001 profile was copied and adapted into the new
canonical UJ_US tree; its customer hypotheses and verification limits were preserved.
