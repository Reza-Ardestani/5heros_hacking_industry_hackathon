# Progress — October 3, 2026

## Shared design tokens — later user request

Delivery check after incorporating remote deployment setup: 32 backend tests
passed, frontend production build passed, and Ruff passed after correcting the
executable bits of two existing shebang scripts. PowerPoint plus unchanged recorded
report/source hash are tracked under docs/demo/presentation/ for teammate access.
Hosted deployment remains a separate acceptance boundary.

Implemented FR-10 / DES-BB-UI-001: 66 JSON-source tokens, generated CSS and scoped
contrast report, generation command wired into frontend prebuild, usage/rationale,
and a browser gallery with explicitly illustrative specimens. Base typography,
navigation colors, actions, evidence badges, focus and motion now consume shared
tokens. Specialized feature/chart CSS still contains literals; migration is partial.

Validation: production TypeScript/Vite build passed; all 21 specified contrast
pairs passed their 4.5:1 text / 3:1 UI thresholds. Regeneration produced identical
CSS/report hashes; all 31 app CSS token references and authored links resolved.
Gallery interaction, computed React action color/font, and default desktop layout
verified in browser; no page overflow or console errors observed. Gallery and app
screenshots saved locally under ignored output/design-tokens/. No whole-app
accessibility, responsive-device, new simulation, or hosted acceptance claim.

## Implemented locally

User authorized early build, then requested guided walkthrough after rejecting
initial UI. Four steps now cover problem, interventions/constraints, simulation,
recommendation. Separate evidence view preserves source/calibration limitations.

- Organizer source copies preserved; selected Discord guidance and team notification
  recorded. Earlier Saturday-noon topic deadline and approval draft captured.
- Problem statement, current-workflow hypothesis, planner journey/stories, design,
  diagrams, constitution and concrete four-file spec established.
- Separate FastAPI backend and React/TypeScript frontend; typed UI contracts, HTTP
  client adapter and reusable presentation components; domain/application/infra
  boundaries; locked Python/npm dependencies and contributing ownership lanes.
- Native SUMO three-junction synthetic corridor. Four actual alternatives,
  outcome-based constrained revision, paired manifests, three evaluation seeds,
  ±20% stress, all-trip accounting and no hidden engine-failure success.
- Editable estimated costs/budget/economic assumptions; constrained recommendation,
  cost-delay Pareto options and JSON report. No trained ML/RL or LLM calls.
- Attributed 500-row Calgary incident context; verified bounded refresh script,
  sourced arrival-profile import; OSM investigative download not used in model.
- Four authentic desktop screenshots and five-minute demo script prepared locally.

## Validation evidence

Commands executed on development macOS arm64, Python 3.12, SUMO 1.27.1:

| Check | Result |
|---|---|
| `cd backend && uv sync --frozen` | Passed; 25 packages checked from lock |
| `cd frontend && npm ci` | Passed; 71 packages audited, zero reported vulnerabilities |
| `make test` | 12 tests passed, 1.71s; Ruff app/tests/scripts passed |
| Test coverage | Bounds/nonfinite input; measured-profile provenance; budget/guardrail/censored rejection; Pareto/economic units; deterministic demand; two real SUMO paired trials; HTTP source/input/404; busy/failure slot release |
| `cd frontend && npm run build` | TypeScript and Vite production build passed |
| Real browser, default run | All four steps, native backend completion, vehicle playback, recommendation, report download passed |
| Independent exported report | All variants share departure SHA256 within each evaluation seed; completed+unfinished+uninserted=planned; all evaluation trips complete |
| Zero-budget API integration | Reference retained; all paid alternatives rejected; completed report exported |
| UI invalid capital budget | Clear Capital budget validation message; rejected input does not start a simulation |
| UI sourced-profile import | Synthetic format fixture imported; weighted rates 975/175 veh/h shown correctly; prior results marked stale; fixture not claimed as measurements |
| Mobile 390×844 | All four steps: no page-wide horizontal overflow; recommendation screenshot inspected |
| Desktop 1440×1000 | Four final step screenshots captured; problem/intervention/recommendation layouts visually inspected |
| Fresh browser console | Zero errors, zero warnings for successful guided run; explicit invalid-input test produced the expected HTTP 422 console entry |
| Refresh CLI | `--limit 0` rejected. `--output-dir output/refreshed-snapshot` downloaded 500 rows and attributed hash without replacing demo source |
| Documentation/source structure | Authored Markdown links resolve; exactly four spec files; handbook original/copy byte-identical |

One nonblocking dependency warning: current Starlette TestClient deprecates httpx
in favor of httpx2. No production/device/host-platform acceptance is implied.
Earlier development hot-reload errors were corrected; final fresh-session check
was clean. Servers are loopback only; histories transient. At this initial
verification, no deployment, commit or push had been performed.

## Recorded experiment — scope matters

[Actual exported evidence](../../../docs/demo/example_result.json), with source,
scenario, per-seed metrics/hashes, trace and stress checks. Default scenario:
900-second arrivals, arterial 1050 veh/h/direction, cross 160 veh/h/direction/junction,
$100,000 budget, cross delay increase capped at 30%, seed 42; evaluation seeds
143/244/345. Reference is synthetic equal green, not observed Calgary timing.

Revision (57.4% usable arterial green) reduced modeled total delay by 27.17%:
196.90s to 143.31s mean vehicle delay. Cross delay rose 14.80%, within guardrail.
Estimated capital $15,000; first proposal failed cross-street guardrail; capacity
option exceeded budget. All evaluation trips completed, both flow stress checks
passed. Selection uses these three evaluation seeds; the reported selected effect
is preliminary, not an independent confirmatory statistical estimate.

## Open gates

- Custom-case organizer acceptance, captain/registration and final form not verified.
- Actual CalTRACS study export, turning/movement mapping and flow calibration absent.
- OSM/signals/observed baseline, safety/constructibility, pedestrians/turns/transit,
  induced demand and engineering cost estimates absent.
- City/consultant user interviews and willingness to pay are hypotheses.
- Canva deck export requested sign-in; not downloaded or fully reviewed. Selected
  Discord guidance is not a complete server export.
- Video/public demo hosting, final submission design package/issue and submission
  remain open. No organizer message or form was sent.

Next team priority: secure organizer validation; source one usable counted corridor;
validate an observed baseline. Preserve this clearly labeled synthetic demonstration
while adding real evidence. Final submission Sunday October 4 noon MDT.

## Git delivery checkpoint — October 3

Prepared initial repository delivery at the user's explicit commit/push request.
Re-ran `make test`: 12 passed in 1.44s; Ruff passed. `make build` passed.
Remote had no branches before this initial commit. Dependencies, generated builds,
logs, raw OSM and raw Discord excerpts are ignored. Recorded field-calibration,
organizer-approval and deployment gates remain open.
