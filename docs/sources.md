# Sources and reuse

Checked/downloaded October 3, 2026 unless a snapshot says otherwise.

| Source | Role and limit |
|---|---|
| [Organizer evidence index](../organizer_docs/README.md) | Local handbook; immutable lab snapshots; selected authenticated Discord channels |
| [Calgary incidents](https://data.calgary.ca/d/35ra-9556) | 500 source rows for context, not measured traffic flow; exact URL/time/hash in data/snapshots/incidents_source.json |
| [Calgary disruption dataset](../data/analysis/README.md) | Six months of incidents (35ra-9556), closures (w8zq-79bq), cameras, signals, travel times, projects, 2024 volumes; hashes in data/analysis/sources_manifest.json. Reported disruptions only |
| [City traffic counts](https://www.calgary.ca/planning/transportation/data/vehicle.html), [CalTRACS](https://trafficcounts.calgary.ca/) | Next calibration source; actual study export remains unavailable in this build |
| [OSM area](https://www.openstreetmap.org/api/0.6/map?bbox=-114.094,51.062,-114.077,51.073), [copyright](https://www.openstreetmap.org/copyright) | Investigative download only; synthetic model does not use OSM |
| [SUMO documentation](https://sumo.dlr.de/docs/index.html), [TripInfo](https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html), [Queue output](https://sumo.dlr.de/docs/Simulation/Output/QueueOutput.html) | Native simulation and outcome definitions; eclipse-sumo 1.27.1 locked |
| [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), [Vite](https://vite.dev/) | Frameworks, separate API and UI; dependency lockfiles committed candidates |
| [uv](https://docs.astral.sh/uv/) | Reproducible Python dependency installation |

Original application source was authored during this event with AI coding
assistance. No organizer starter application or RadarCX application code was
copied. RadarCX contributed the constitution/four-file spec documentation pattern.
Organizer reference files remain verbatim; upstream LICENSE preserved with its
snapshot. SUMO is EPL-2.0/GPL-2.0 licensed; React, Vite, FastAPI and Lucide retain
their respective package licenses. Do not remove dependency license notices when
distributing bundles. No new project license has been chosen on the team's behalf.

Optional Google Fonts stylesheet in frontend/src/style.css has system-font
fallbacks; the prototype can run without that network request. No participant
photos, unrelated chat logs, credentials or model-provider keys are distributed.
