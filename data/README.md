# Data and calibration

## Public incident snapshot

[Calgary Traffic Incidents](https://data.calgary.ca/d/35ra-9556) exposes public
[JSON](https://data.calgary.ca/resource/35ra-9556.json) and
[GeoJSON](https://data.calgary.ca/api/views/35ra-9556/rows.geojson?accessType=DOWNLOAD).
No token was needed for the bounded 500-row download used here. Source URL,
retrieval time, exact payload SHA256, row count and City license attribution live
in snapshots/incidents_source.json. `python3 scripts/refresh_incidents.py` refreshes
it; stop the API first to avoid reading the two-file pair during replacement.

Rows are sorted by start time and may describe cleared incidents. Coordinate
updates can produce multiple records. The adapter keeps the latest description
for normalized title + start timestamp: a heuristic, not an authoritative event ID.
No incident duration, measured flow, worst-congestion ranking or intervention
impact is inferred from these records. Snapshot data is only context in the UI;
it does not alter simulation demand or choose the modeled corridor.

## Six-month disruption dataset

Incidents, closures and reference layers for April–October 2026, with JSON,
Excel, parsing rules and the prediction backtest: [analysis/README.md](analysis/README.md).

## Traffic flow — required next evidence

[CalTRACS](https://trafficcounts.calgary.ca/) provides City traffic-count studies;
[City explanation](https://www.calgary.ca/planning/transportation/data/vehicle.html).
Use dated directional/turning counts for the selected study location and intervals.
An actual CalTRACS spreadsheet has **not** been downloaded or calibrated in this
build. The site's config was reachable; a guessed TCStudy endpoint timed out.
Do not advertise a working flow API based on that probe.

Ask the data owner to select/export one study in CalTRACS, preserve its original
workbook under ignored raw/, record its study/date/URL and movement mapping, then
normalize its units. Counts from different years/seasons/time periods are not
interchangeable. A 15-minute count of 225 vehicles is 900 vehicles/hour, not 225.

## Arrival-profile import contract

The UI accepts JSON containing `demand_source`, `duration_s`, `flow_profile`:

```json
{
  "demand_source": "Actual study URL, date, location and movement mapping",
  "duration_s": 900,
  "flow_profile": [
    {"begin_s": 0, "end_s": 900, "main_vph": 900, "cross_vph": 150}
  ]
}
```

The numbers above demonstrate syntax only; they are not measured Calgary counts.
Up to 12 contiguous ordered intervals, starting at zero, covering the entire
300–1800 second demand window. Rates are **per direction** on the arterial and
**per direction at each junction** on the cross streets. In the synthetic model,
all three cross streets share one rate: do not import combined network totals or
an asymmetric turning study without an explicit transformation/limitation.
Server limits: main rate 0–1800; cross rate 0–600 veh/h in profile intervals;
nonzero traffic required. Scalar synthetic rates have minimums 50 and 20.

The UI marks an imported profile as user-supplied measured arrivals. This label
is a provenance declaration, not automatic validation of the study. Profile
average shown in controls is weighted by interval duration. Geometry remains
synthetic. Measured arrivals alone do not calibrate queues, route choices or
travel time. Advanced inputs show the submitted profile in the final report.

## Network

An OSM area around 16 Avenue/10 Street NW was downloaded for investigation
(bbox -114.094,51.062,-114.077,51.073). It is **not used by this prototype**.
Metadata: [network source](network_source.json). Raw OSM ignored to keep the
repository small. [Download area](https://www.openstreetmap.org/api/0.6/map?bbox=-114.094,51.062,-114.077,51.073).
© OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright).

Before using an OSM import, inspect lane/movement/signal mappings; generated
signals are not observed Calgary timings. Obtain actual phases, turns, transit,
pedestrian demand, queues and travel times; fit baseline first. Hold back a
measurement period and only then compare interventions on identical demand.

## What the simulator measures

Actual SUMO output, not mocked results:

- Delay: `timeLoss + departDelay` in seconds; SUMO timeLoss is relative to desired
  free-flow driving, not route travel-time difference between network designs.
- Mean delay uses every planned vehicle. Uninserted vehicles contribute their
  horizon waiting; unfinished/uninserted comparisons are rejected for effectiveness.
- Queue metric: maximum across sampled timestamps of summed lane queue lengths
  in **metres**. Not queue vehicle counts or peak single-intersection length.
- Vehicle-position playback: optimization seed, every 10 seconds, capped at 150
  vehicles/frame. Outcome table averages three paired evaluation seeds instead.
- Costs in CAD are editable estimates. Annual time valuation repeats only this
  modeled period on the assumed operating days; it is not full-day demand scaling.

Costs, value of time, occupancy, asset life and operating days need cited estimates
for a City-facing pilot. No cost quote, construction feasibility or safety approval
has been obtained. Scientific validation requires more seeds and observed baselines.

To verify a fresh download without replacing the demo snapshot:
`python3 scripts/refresh_incidents.py --output-dir output/refreshed-snapshot`.
The development verification downloaded 500 rows successfully to that ignored folder.
