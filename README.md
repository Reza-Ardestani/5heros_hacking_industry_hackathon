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
arm64 and Windows 11 (x64); other systems remain untested. Initial setup downloads SUMO
and its data.

**One command, any OS (Windows included, no `make` needed)** — starts the API, the UI and
the MCP server, installing dependencies on first run:

```sh
python scripts/dev.py
```

| What | URL |
|---|---|
| UI | http://localhost:5173 |
| API docs | http://127.0.0.1:8008/docs |
| MCP endpoint (streamable HTTP, stateless) | http://127.0.0.1:8000/mcp |
| MCP self-description | http://127.0.0.1:8000/mcp-info (`?check=true` runs a live self-test) |
| Same, via the API (used by the UI's `mcp-info-ml` tab) | http://127.0.0.1:8008/api/mcp-info |
| Chat (the dock at the bottom right of the UI) | `POST http://127.0.0.1:8008/api/chat` |

The chat answers with the same MCP tools and moves the UI ("top 5 hotspots in SE",
"forecast Stoney Trail next 14 days", "simulate Glenmore Trail & Macleod Trail", "go to
evidence"). It runs without any key. Optional: set `ANTHROPIC_API_KEY` in the API's
environment for free-form questions answered by Claude (`claude-opus-5-5`) using the
same tools; `BB_CHAT_MODE=builtin` turns that off. Never commit the key.

`python scripts/dev.py --check` starts everything, verifies the UI, API, MCP protocol and
`mcp-info`, then stops (exit code 1 on any failure). Ports in use? Add
`--api-port 8108 --web-port 5273 --mcp-port 8100`. Connect Claude Code to the MCP server
with `claude mcp add --transport http calgary-disruptions http://127.0.0.1:8000/mcp`.

Or, with `make`, step by step:

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
This local server has no authentication; the deployed container adds a shared password.

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

Build output is frontend-only; `make web` uses Vite's `/api` proxy. For deployment,
`app.deploy:app` serves the API and built frontend together (see below).

## Free demo in GitHub Codespaces (no card)

On GitHub: **Code → Codespaces → Create codespace on this branch**. The
[devcontainer](.devcontainer/devcontainer.json) installs everything and starts the app on
port 8080 (UI + API behind a shared password, user `bottleneck`; set the
`BB_AUTH_PASSWORD` Codespaces secret, or one is generated and printed). The MCP server
runs on port 8000. To share: Ports tab → right-click 8080 → Port Visibility → Public.
Switch branch from the terminal with `bb-start <branch>` (any branch with
`backend/app/deploy.py`). Free accounts get 120 core-hours a month; idle codespaces stop.

## Optional: ElevenLabs voice for chat replies

Set `ELEVENLABS_API_KEY` in the API's environment (in Codespaces: a Codespaces secret,
then restart with `bb-start`) and each assistant reply gets a read-aloud button. The
backend calls ElevenLabs text-to-speech (`POST /api/speech`, MP3), so the key never
reaches the browser. Optional: `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL`. Without a key
the button is hidden and nothing else changes. Never commit the key.

## Deploy (Google Cloud Run)

One container ([Dockerfile](Dockerfile)) serves the API and built frontend behind a
shared password (user `bottleneck`, password in Secret Manager). It runs as a single
instance because jobs are in memory, and scales to zero when idle.

1. Once: `PROJECT_ID=<project> REGION=us-central1 bash deploy/setup-gcp.sh`, then add the
   four repository variables it prints.
2. Push any branch. [The workflow](.github/workflows/deploy.yml) smoke-tests the image and
   deploys it as a revision tagged with the branch name, at
   `https://<branch-tag>---<service-url-host>`. Pushes to `main` also take the main URL.
3. Point the main URL at another branch instantly (no rebuild):
   `gcloud run services update-traffic bottleneck-busters --region <region> --to-tags <branch-tag>=100`

## What works

- Guided problem/intervention/simulation/recommendation flow, with separate evidence view.
- Editable flows, capital costs, budget, cross-street guardrail and economic assumptions.
- Source-attributed measured-arrival JSON import; explicit synthetic defaults.
- Actual baseline, first plan, outcome-based revision and lane-capacity experiment.
- Three paired evaluation seeds, ±20% sensitivity checks, full trip accounting.
- SUMO vehicle-position playback, agent trace, cost/delay frontier, rejection reasons.
- Exportable JSON report with inputs, hashes, per-seed metrics, assumptions and sources.
- Chat dock that answers with the MCP tools and navigates pages, intersections and forecasts.

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
