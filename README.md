# Bottleneck Busters — Intervention Lab

A working local decision-support prototype for Calgary transportation planning.
Compare signal retiming and lane-capacity alternatives against an equal-green
reference, within a capital budget and cross-street delay guardrail. Policy agents
run actual SUMO simulations, revise an unsafe first proposal, evaluate frozen
plans on paired arrival manifests and export evidence. No trained RL or LLM is
required for this first experiment.

**Evidence scope:** real Calgary incident context; synthetic corridor and default
traffic arrivals. The prototype demonstrates a planning method, not a verified
improvement on Calgary roads. Actual counts, signal timings, movements and observed
queues/travel times are required before any field-benefit claim.

## Run locally

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.js 20.19+ or 22+,
macOS/Linux/Windows supported by the SUMO wheel. Native SUMO was verified on macOS
arm64; other systems remain untested. Initial setup downloads SUMO and its data.

```sh
cd /path/to/5heros_hacking_industry_hackathon
make setup
make api
```

In a second terminal, from the repository root:

```sh
make web
```

Open [Intervention Lab](http://127.0.0.1:5173), then follow **Problem → Interventions → Simulation → Recommendation**. API docs:
[localhost:8008/docs](http://127.0.0.1:8008/docs). One run executes 20 real simulation
trials; the default took approximately 12 seconds on the development Mac.

No Make available: run the commands listed in [Makefile](Makefile) individually.
No API key or .env file required. Servers bind loopback. Jobs are in memory,
limited to one active run and eight retained jobs; restarting the API loses history.
This local server has no authentication or production deployment configuration.

```sh
make test
make build
# Stop API before refreshing the two-file source snapshot.
make refresh
```

Calgary disruption data (Intersections view, database, MCP tools —
[design](docs/design/disruption-data/design.md)):

```sh
make disruptions    # backfill six months into data/db/disruptions.sqlite + export JSON/XLSX
make collect        # one incremental poll; make collect-loop polls every 5 minutes
make mcp            # MCP server over stdio; make mcp-http serves 127.0.0.1:8000/mcp
```

A fresh checkout seeds its database from the committed `data/analysis` exports.

Build output is frontend-only; `make web` uses Vite's `/api` proxy. A deployed
frontend requires a separate API proxy/server configuration.

## What works

- Guided problem/intervention/simulation/recommendation flow, with separate evidence view.
- Editable flows, capital costs, budget, cross-street guardrail and economic assumptions.
- Source-attributed measured-arrival JSON import; explicit synthetic defaults.
- Actual baseline, first plan, outcome-based revision and lane-capacity experiment.
- Three paired evaluation seeds, ±20% sensitivity checks, full trip accounting.
- SUMO vehicle-position playback, agent trace, cost/delay frontier, rejection reasons.
- Exportable JSON report with inputs, hashes, per-seed metrics, assumptions and sources.

In the recorded default experiment, revision reduced total modeled delay by
27.17%, with cross-street mean delay up 14.80% within a 30% guardrail. The $15,000
cost is an editable assumption. All trips completed in the three evaluation seeds;
both demand stress checks passed. These are preliminary simulation results, not
observed City savings. [Recorded evidence](docs/demo/example_result.json).

## Project map

- [Organizer sources and changed deadlines](organizer_docs/README.md).
- [Problem, algorithm and pilot hypothesis](docs/problem_statement.md).
- [User journey](docs/user_journeys/planner.md), [stories](docs/user_stories/planning.md),
  [modeling index](docs/modeling.md).
- [Design](docs/design/bottleneck-lab/design.md), [architecture](docs/diagrams/architecture.md),
  [execution sequence](docs/diagrams/run_sequence.md).
- [Constitution](constitution/mission.md), [MVP contract](specs/features/phase-1-hackathon-mvp/requirements.md),
  [verified progress](specs/features/phase-1-hackathon-mvp/progress.md).
- [Data, units and missing calibration](data/README.md), [contributing](CONTRIBUTING.md),
  [five-minute demo](docs/demo/demo_script.md).

## Event status

Discord team notification names Bottleneck Busters and a custom Energy and
Infrastructure case. Organizer acceptance and captain/registration remain
unverified. Updated topic deadline: **October 3, noon MDT**; final submission:
**October 4, noon MDT**. No organizer message, submission or deployment
has been performed by this build. [Approval request draft](organizer_docs/approval_message_draft.md).

Documentation structure was adapted from RadarCX; no RadarCX application code or
business/database requirements were copied. Organizer materials and dependencies
retain their own licenses. [Source and dependency attribution](docs/sources.md).
