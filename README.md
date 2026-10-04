# Bottleneck Busters

### Which Calgary bottlenecks keep us stuck?

**Explore disruptions. Test interventions. Explain the tradeoffs.**

Bottleneck Busters helps Calgary mobility planners investigate traffic disruptions
and compare signal and road-capacity changes within budget. An agent runs real
SUMO simulations, revises unsuitable proposals, and explains modeled delay and
cross-street impacts with an auditable report.

**Industry Hackathon · Energy and Infrastructure Systems · Custom case**

[User journeys](#user-journeys) · [Architecture](#architecture-and-design) ·
[Dataset](#dataset) · [Results](#results) · [Run locally](#run-locally)

## Introduction and problem statement

A congested commute is easy to feel. Choosing an intervention is harder: is the
problem recurring, driven by construction, or tied to a particular intersection?
Would a cheaper signal change help? Would it make cross-street travel worse?

Our teammate Amy Miller's experience of Calgary traffic inspired the project.
[Discovery conversations](validation_market_research/README.md) highlighted the
need to distinguish recurring bottlenecks from temporary disruption and justify
investments through costs, public impacts, assumptions, and tradeoffs.

Our core question: **which changes could reduce delay within budget while
protecting cross-street travel?** The lab connects City disruption context to a
repeatable propose, simulate, evaluate, and revise workflow. It gives planners
alternatives and evidence they can inspect before pursuing engineering review.

> **Evidence scope:** Calgary disruption records are real. The simulation corridor
> and default traffic arrivals are synthetic. Improvements are modeled, not
> field-proven; measured counts, signal timings, queues, and travel times are
> needed before claiming benefits on Calgary roads.

## User journeys

1. **Monitor the city and selected areas.** Explore intersections, City-reported
   incidents and closures, historical patterns, and area or road filters. Use
   disruption evidence to choose locations worth investigating.
2. **Configure a study.** Set demand, budget, estimated costs, and cross-street
   protection limits. Choose signal retiming, capacity, clearance, or turn options;
   import a source-attributed arrival profile when measured counts are available.
3. **Find, test, and justify an intervention.** Use forecasts to prioritize
   investigation, then compare interventions in SUMO against equivalent reference
   inputs. Inspect the agent's revisions, cost/delay frontier, rejection reasons,
   playback, and exportable evidence.

The guided workspace follows **Problem → Interventions → Simulation → Recommendation**,
with a separate evidence view. The chat dock can answer through MCP tools and move
between studies, intersections, and forecasts; the default mode needs no API key.

[Planner journey and stories](UJ_US/README.md) ·
[Five-minute demo](docs/demo/demo_script.md)

## Architecture and design

![Bottleneck Busters architecture at a glance: Calgary data, ingestion, storage, backend, and React frontend](submission_artifacts/07-architecture-overview.png)

City data feeds a shared evidence store. The Python backend exposes HTTP and MCP
tools, coordinates the intervention agent, and runs SUMO trials. React presents
maps, studies, comparisons, forecasts, and chat.

The diagrams show the Codespaces demo layout. The same components run locally.
**SQLite is the default database and durable write journal. TimescaleDB is
configurable:** synchronized reads use its PostgreSQL mirror; outages fall back
to SQLite and queue changes for ordered replay.

<details>
<summary><strong>Inside the backend: tools, agent loop, and simulation</strong></summary>

![Bottleneck Busters system architecture showing MCP tools, the proposal/evaluation/revision loop, and SUMO baseline/trials](submission_artifacts/06-architecture.png)

</details>

| Layer | Responsibility |
|---|---|
| React / TypeScript / Vite | Vertical slices for studies, intersections, forecasting, assistant, and storage; shared transport and design tokens |
| Python / FastAPI | Validated HTTP inputs, bounded jobs, application services, and entry-point dependency wiring |
| Domain and agent loop | Constraints, budget, paired evaluation, forecast selection, costs, and proposal revision |
| Infrastructure | SUMO subprocesses, City feeds, SQLite/Timescale adapters, run logs, MCP gateway, and optional Claude adapter |
| MCP server | Shared disruption and study tools, streamable HTTP or stdio, and live self-description |

Backend dependencies point inward through explicit ports. Frontend slices expose
public entry points. Both boundaries have static checks under `make architecture`.
Pydantic contracts, process-local jobs/caches, and a single SQLite authority remain
intentional hackathon compromises.

[Backend boundaries](docs/design/clean-architecture.md) ·
[Frontend slices](docs/design/frontend-vertical-slices.md) ·
[Execution sequence](docs/diagrams/run_sequence.md) ·
[Storage recovery](docs/ops/storage.md)

## Dataset

The October 3 snapshot covers April–early October 2026 and combines **eight City
of Calgary sources**: incident history, current incidents, detours, construction
projects, cameras, signals, travel times, and 2024 traffic volumes.

- **3,987 deduplicated incidents** and **270 distinct closures** in committed exports.
- JSON evidence, a 20-sheet Excel workbook, and source URLs, retrieval times, and
  payload hashes make the preparation inspectable.
- A fresh checkout seeds SQLite from these exports. Incremental collection adds
  new sightings; rebuilding the demo does not require another City download.

These records describe **reported disruptions**. They do not directly measure
congestion, clearance duration, intervention impact, or exposure-adjusted crash
risk. Older completed closures can be missing from the City's current detour feed.

Forecasts compare flat daily-average, empirical-Bayes, and LightGBM models on the
same chronological inputs. Selection uses validation days before test scoring;
no model wins everywhere. Forecasts support investigation, while SUMO supports
modeled intervention comparison.

[Dataset, preparation, and backtests](data/analysis/README.md) ·
[Source manifest](data/analysis/sources_manifest.json) ·
[Arrival profiles and calibration gaps](data/README.md)

## Results

The recorded synthetic default experiment selected a revised signal plan against
an **equal-green reference**, using three paired hold-out seeds and ±20% demand
stress checks.

| Recorded outcome | Value |
|---|---|
| Total modeled delay reduction | **27.17%** |
| Cross-street mean delay increase | **14.80%**, within the configured 30% guardrail |
| Retiming capital cost | **CAD 15,000**, an editable assumption |
| Trip accounting | All trips completed across the three evaluation seeds |
| Demand sensitivity | Both recorded stress checks passed |

These are preliminary simulator outputs for the recorded inputs, not observed
City savings. The report includes per-seed metrics, demand/network hashes,
assumptions, sources, and rejected alternatives.

[Recorded result](docs/demo/example_result.json) ·
[Metric definitions](data/README.md#what-the-simulator-measures) ·
[Current implementation evidence](constitution/progress.md)

## Challenges and future work

- **Calibrate before field claims.** Obtain a dated CalTRACS count study, observed
  timings, movements, queues, and travel times; inspect the network and fit the
  reference before comparing alternatives.
- **Improve forecast uncertainty.** Sparse selections can lose to a flat average;
  Poisson ranges need stronger treatment of day-to-day variability.
- **Validate feasibility and economics.** Intervention costs are estimates.
  Materials, equipment, maintenance, and availability integrations remain planned.
- **Move beyond the demo.** Durable jobs, managed storage/collection, broader
  simulation coverage, and consultant pilots remain future work. The storage
  design requires one shared SQLite authority; independent ephemeral replicas
  need a different persistence design.

[Roadmap](constitution/roadmap.md) · [Modeling decisions](docs/modeling.md)

## Team and project documentation

Abdelrahman Ahmed Ali Ahmed ([@AbdelrahmanSuliman](https://github.com/AbdelrahmanSuliman)) ·
Amy Miller ([@Amesandfire](https://github.com/Amesandfire)) ·
Praneetha Rajupalepu ([@PraneethaRajupalepu](https://github.com/PraneethaRajupalepu)) ·
Reza Ardestani ([@Reza-Ardestani](https://github.com/Reza-Ardestani)) ·
Sumit Gupta ([@sumitgupta477](https://github.com/sumitgupta477))

[Constitution](constitution/mission.md) · [Feature specs](specs/features/) ·
[Contributing](CONTRIBUTING.md) · [Organizer guidance](organizer_docs/README.md) ·
[Sources and reuse](docs/sources.md)

Application code was authored during the event with AI coding assistance. RadarCX
provided the documentation structure; its application code and product/database
requirements were not copied. Data and dependencies retain their own licenses.
Organizer acceptance and final submission are separate from local build evidence;
see the organizer index for the recorded status and sources.

## Run locally

### Prerequisites

Install **Python 3.12+**, **uv**, **Node.js 20.19+ or 22+**, and **npm**. The commands
below use Make on macOS/Linux or a shell with Make installed. SUMO is installed
through the pinned Python dependency; macOS arm64 and Windows x64 were previously
verified. Linux may need native OpenGL/X libraries; the
[Codespaces setup](.devcontainer/devcontainer.json) lists those dependencies.

Clone the repository with your GitHub access, then run commands from its root:

```sh
git clone https://github.com/Reza-Ardestani/5heros_hacking_industry_hackathon.git
cd 5heros_hacking_industry_hackathon
make help
```

### Start backend and frontend together

```sh
make dev
```

Installs locked dependencies, starts **API + frontend + MCP**, and prints URLs.
Stop all three with **Ctrl+C**. No API key, Docker, or .env file is required for
this default SQLite demo. First setup downloads Python/SUMO and npm packages.

| Service | Local address |
|---|---|
| Frontend | http://127.0.0.1:5173 |
| Backend API docs | http://127.0.0.1:8008/docs |
| API health | http://127.0.0.1:8008/api/health |
| MCP endpoint | http://127.0.0.1:8000/mcp |
| MCP self-description | http://127.0.0.1:8000/mcp-info |
| MCP information via API | http://127.0.0.1:8008/api/mcp-info |

For Windows or a system without Make, the same launcher is available directly:

```sh
python scripts/dev.py
```

### Start backend and frontend separately

Install dependencies once:

```sh
make setup
```

**Terminal 1 — backend**, from the repository root:

```sh
make api
```

**Terminal 2 — frontend**, from the repository root:

```sh
make web
```

Open http://127.0.0.1:5173. Vite proxies `/api` to port 8008. To use the standalone
MCP endpoint and live MCP diagnostics, run `make mcp-http` in a third terminal.
Chat's in-process tools work without that separate server.

### Check startup, tests, and build

```sh
make dev-check       # Start services, check UI/API proxy/MCP, then stop
make test-backend    # Backend pytest suite; optional Timescale tests require opt-in
make test-web        # Frontend tests and slice guard
make architecture    # Backend + frontend boundary checks
make build           # TypeScript/Vite production build in frontend/dist
```

`make test` also runs backend Ruff; the last recorded full lint has four existing
executable-mode errors. Detailed scope and skipped tests are in the
[backend](specs/features/clean-architecture-boundaries/progress.md) and
[frontend](specs/features/frontend-vertical-slices/progress.md) evidence.

If default ports are occupied, use the combined launcher with alternatives:

```sh
make dev DEV_ARGS="--api-port 8108 --web-port 5273 --mcp-port 8100"
# If your Python command is named python:
make dev PYTHON=python
```

### Optional data collection, tools, and storage

```sh
make collect         # One incremental City poll; network required
make collect-loop    # Poll every five minutes
make disruptions     # Six-month backfill plus JSON/XLSX exports
make mcp             # MCP over stdio for a local agent client
```

`make refresh` replaces the incident snapshot; stop the API first. Collection is
optional for the initial demo because committed exports seed the local database.

For **TimescaleDB with durable SQLite fallback**, start Docker, copy the example
environment file, and replace both matching password placeholders before startup:

```sh
cp .env.timescale.example .env.timescale
# Edit .env.timescale: replace both matching password placeholders.
make db-up
make db-sync
make dev-timescale
```

Keep credentials out of Git. Preserve the SQLite directory and Timescale volume.
[Storage setup, recovery, and deployment limits](docs/ops/storage.md) explain the
single-authority design and optional database verification.

Optional Claude chat reads `ANTHROPIC_API_KEY` from the backend environment;
`BB_CHAT_MODE=builtin` selects the key-free mode. Local services bind loopback and
have no authentication. Jobs are in memory: restarting the API loses active and
retained job handles, while study evidence remains in database tables/run logs.

### Hosted demo options

[Codespaces configuration](.devcontainer/devcontainer.json) starts the combined
UI/API on port 8080 behind a shared password, plus MCP on port 8000. The username
is `bottleneck`; use the `BB_AUTH_PASSWORD` Codespaces secret or the generated
password printed by the launcher. The Ports panel controls sharing visibility.

The [Dockerfile](Dockerfile), [Cloud Run setup](deploy/setup-gcp.sh), and
[deployment workflow](.github/workflows/deploy.yml) provide the container route.
The frontend build alone does not start a server; `app.deploy:app` serves the
built UI and API together. Local checks do not establish hosted deployment or
field acceptance.
