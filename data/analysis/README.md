# Calgary traffic disruption dataset — six months

Built October 3, 2026 by `scripts/build_disruption_dataset.py` from the City of
Calgary Open Data feeds behind the
[traffic cameras page](https://www.calgary.ca/roads/conditions/traffic-cameras.html)
(its camera map, "Traffic report" and travel-time links resolve to data.calgary.ca).
Contains information licensed under the Open Government Licence – City of Calgary
([terms](https://data.calgary.ca/stories/s/Open-Calgary-Terms-of-Use/u45n-7awa)).

**Storage:** the canonical copy is the SQLite database `data/db/disruptions.sqlite`
(git-ignored). The files in this folder are exports of it, committed so a fresh checkout
can seed its database offline. Schema, collector and MCP tools:
[design](../../docs/design/disruption-data/design.md).

**What this data is:** reported disruptions observed by City camera operators,
plus scheduled closures. **What it is not:** traffic flow, delay, congestion, or
exposure-adjusted crash risk. It helps choose *which* corridor to study; the
simulator still needs measured counts and timings for that corridor.

Window: **2026-04-01 00:00 MDT → 2026-10-03 18:17 UTC** (186 calendar days; six
complete months April–September plus 3 days of October).

## Datasets used (8)

| # | City dataset | ID | Rows pulled | Role |
|---|---|---|---:|---|
| 1 | Traffic Incidents (unofficial archive) | [35ra-9556](https://data.calgary.ca/d/35ra-9556) | 4,070 | Six-month incident history (main table) |
| 2 | Current Traffic Incidents | [4jah-h97u](https://data.calgary.ca/d/4jah-h97u) | 1 | Snapshot; the UI also reads it live |
| 3 | Construction Detours (road/lane closures) | [w8zq-79bq](https://data.calgary.ca/d/w8zq-79bq) | 271 | Scheduled closures (270 distinct); UI reads active ones live |
| 4 | Road Construction Projects | [sizs-hgef](https://data.calgary.ca/d/sizs-hgef) | 11 | Major project context |
| 5 | Traffic Cameras | [k7p9-kppz](https://data.calgary.ca/d/k7p9-kppz) | 216 | Nearest camera + live JPEG per intersection |
| 6 | Traffic Signals | [qr97-4jvx](https://data.calgary.ca/d/qr97-4jvx) | 1,791 | Signalized-intersection match (≤ 75 m) |
| 7 | Travel Times | [aeb8-fh2w](https://data.calgary.ca/d/aeb8-fh2w) | 68 | Point-in-time corridor travel times |
| 8 | Traffic Volumes for 2024 | [cauu-7hnw](https://data.calgary.ca/d/cauu-7hnw) | 334 | Segment daily volume for rough exposure |

**Total pulled: 6,762 source rows.** Exact query URLs, retrieval time and SHA256 of
every raw payload are in [sources_manifest.json](sources_manifest.json). Raw
payloads are kept verbatim in `data/raw/calgary_disruptions/` (git-ignored).

Closure history caveat: the City's detour feed lists only current and scheduled
closures (earliest start in feed 2025-06-01). Closures that finished before
retrieval are not retained, so past short closures are missing; 208 of 270 overlap
the window. No City archive of past closures was found. The collector now records
when each closure leaves the feed, so history builds up from October 3 onward.
271 rows → 270 closures: one closure was posted twice with identical text and dates
about 25 m apart. Several other closures share a location and start time but differ
by direction or lane, so the description is part of each closure's identity.

## Output files

| File | Contents | Size |
|---|---|---:|
| `calgary_incidents_6mo.json` | 3,987 deduplicated, parsed and geo-enriched incidents (38 fields each) | 5.7 MB |
| `calgary_closures.json` | 270 classified closures with nearest signal/camera, first/last seen | 0.3 MB |
| `calgary_context_layers.json` | Current incidents, projects, travel times, cameras, signals, 2024 volumes | 0.5 MB |
| `calgary_disruption_summary.json` | All aggregates below + data-quality block + category rules | 0.2 MB |
| `calgary_disruptions_analysis.xlsx` | 20-sheet workbook (README, Sources, Headline & quality, By category, Monthly trend, Hour x weekday, By period, By quadrant, Lane impact, Top corridors, Top intersections, Signal hotspots, Camera hotspots, Incidents, Closures, Closure summary, Current incidents, Construction projects, Travel times, Category rules) | 1.1 MB |
| `sources_manifest.json` | Source URLs, row counts, hashes, licence, window | 3 KB |

**Data points added:** 3,987 incidents × 38 fields = 151,506 incident values;
270 closures, ~33 fields each; plus 2,421 reference rows
(216 cameras, 1,791 signals, 334 volume segments, 68 travel times, 11 projects,
1 current incident). 1,750 distinct intersections and 199 routes
(≥ 3 incidents) are indexed for the UI.

## How each record is parsed

Pipeline per incident row:

1. **Download** with `$where start_dt_utc >= window start`, keep raw bytes + SHA256.
2. **Validate** coordinates inside the Calgary region (0 discarded).
3. **Deduplicate** on normalized location text + start time, keeping the latest
   update (same heuristic as `backend/app/infra/incidents.py`): 4,070 → 3,987
   (83 coordinate/description updates removed). Heuristic, not an official ID.
4. **Time:** UTC → America/Edmonton; derive date, month, season, weekday, hour and
   period (AM peak 06:30–09:00, Midday, PM peak 15:00–18:30, Evening/overnight,
   Weekend). `update_lag_min` = last update − start; **not** clearance time.
5. **Category:** first matching regex on the City's free-text description (rules in
   the summary JSON and the *Category rules* sheet). 19 categories in 9 groups.
6. **Lane impact / lane position:** from phrases such as "Blocking the right lane",
   "multiple lanes", "road is closed", "shoulder".
7. **Location:** strip direction word ("Northbound …") and quadrant suffix, split on
   *and / at / approaching / between …*, normalize abbreviations (Tr→Trail,
   Av→Avenue, Bv→Boulevard …). Bare names are aliased to their dominant full
   name (Deerfoot→Deerfoot Trail, Stoney→Stoney Trail, Macleod→Macleod Trail,
   Crowchild→Crowchild Trail, Metis→Metis Trail, Douglasdale, Dalhousie).
   *Corridor key* = primary road, plus quadrant for numbered streets/avenues
   (9 Avenue SE ≠ 9 Avenue SW). *Intersection key* = the two roads sorted + quadrant.
8. **Geo-enrichment:** nearest City signal (≤ 75 m → `at_signalized_intersection`),
   nearest camera (≤ 500 m flag), and 2024 segment volume — only from a segment on
   the **same road** within 150 m (at interchanges the nearest segment is usually
   the crossing freeway, which inflated volumes in the first build).

### Real examples (raw → parsed)

| Raw `incident_info` / `description` (UTC) | Parsed |
|---|---|
| "Eastbound 32 Avenue at 32 Street NE" / "Two vehicle incident. Blocking the right lane" / 2026-04-02 12:45 | 06:45 Thu, AM peak · Collision → Two-vehicle collision · Single lane blocked, **Right lane**, EB · corridor *32 Avenue NE* · intersection *32 Avenue & 32 Street NE* · signal 10 m away · camera 107 at 437 m |
| "Northbound Deerfoot and 64 Avenue NE" / "Multi-vehicle incident. Blocking multiple lanes" | PM peak · Multi-vehicle collision · Multiple lanes, NB · corridor *Deerfoot Trail* (alias) · *64 Avenue & Deerfoot Trail NE* · not signalized (freeway) |
| "4 Avenue approaching 3 Street SE" / "Stalled vehicle. Blocking the left lane" | Midday · Vehicle breakdown → Stalled vehicle · **Left lane** · corridor *4 Avenue SE* · signalized · 2024 volume 22,000 veh/day |
| "Valiant Drive and Shaganappi Trail NW" / "There is an incident involving a pedestrian- EMS on site." | 20:13 · Vulnerable road user → Pedestrian involved · EMS flag · lane not reported |
| "Country Hills Boulevard and Stoney Trail NW" / "Traffic signals are flashing red." | PM peak · Signal fault → Signals flashing red |

Closures are classified the same way (`closure_type`: lane closure, full road
closure, ramp, speed restriction, sidewalk/cycle, turn restriction; flags for
signed detour, time-restricted work, multi-lane) with status at retrieval
(Active / Scheduled / Ended) and whether they overlap the window.

## Summary of the data

**Headline:** 3,987 incidents · 21.4 per day · 43.2% blocked at least one lane ·
46.7% within 75 m of a City signal · 49.0% within 500 m of a camera · one day
with no records at all (2026-09-17, treated as a data gap).

| Month | Incidents | Days | Per day |
|---|---:|---:|---:|
| 2026-04 | 634 | 30 | 21.1 |
| 2026-05 | 646 | 31 | 20.8 |
| 2026-06 | 635 | 30 | 21.2 |
| 2026-07 | 722 | 31 | 23.3 |
| 2026-08 | 650 | 31 | 21.0 |
| 2026-09 | 647 | 29 | 22.3 |
| 2026-10 (partial) | 53 | 3 | 17.7 |

| Category | Incidents | Share | Lane-blocking |
|---|---:|---:|---:|
| Traffic incident (unspecified) | 2,404 | 60.3% | 732 |
| Two-vehicle collision | 585 | 14.7% | 445 |
| Multi-vehicle collision | 285 | 7.2% | 240 |
| Pedestrian involved | 252 | 6.3% | 46 |
| Stalled vehicle | 127 | 3.2% | 102 |
| Single-vehicle collision | 100 | 2.5% | 79 |
| Signals flashing red / blank / other / power / work | 125 | 3.1% | 3 |
| Cyclist involved | 45 | 1.1% | 17 |
| Unplanned road/ramp closure | 42 | 1.1% | 38 |
| Hazard, police, utility, other | 22 | 0.6% | 20 |

By quadrant: SE 1,275 · NE 1,118 · NW 808 · SW 786. By period: PM peak 1,020 ·
Midday 903 · Weekend 856 · Evening/overnight 720 · AM peak 488. Busiest hours:
17:00 (384) and 16:00 (372). Lane impact: not reported 2,196 · single lane 1,246 ·
multiple lanes 400 · full closure 76 · shoulder 69.

Top corridors: Deerfoot Trail 383 · Stoney Trail 295 · Glenmore Trail 186 ·
Crowchild Trail 110 · 16 Avenue NE 101 · Macleod Trail 97. Top intersections:
Deerfoot & Glenmore SE 77 · 17 Avenue & Deerfoot SE 66 · 16 Avenue & Deerfoot NE 63 ·
Deerfoot & Memorial SE 61 · Deerfoot & Peigan SE 34 · 14 Street & Glenmore SW 30.

Closures (status evaluated at read time): 204 active, 62 scheduled, 4 ended;
overlapping the window: 125 lane closures/reductions, 48 full road closures, 7 ramp
closures, 6 speed restrictions, 22 other.

`incidents_per_10k_daily_veh` in *Top corridors* divides incidents by the median
matched 2024 volume when ≥ 5 incidents matched a volume segment. It is a rough
exposure normalisation (2024 volumes, 2026 incidents), not a crash rate.

## Prediction models (used by the UI)

Three models compete per selection (`backend/app/domain/forecast.py`): flat daily average
(baseline), weekday × period empirical-Bayes rates, and **LightGBM** Poisson
gradient-boosted trees (`backend/app/domain/ml_forecast.py`; features: weekday, period,
weekend, Alberta holiday, trend, citywide cell rate, Bayes rate). The model is chosen on
the 28 validation days before the 28 test days, then refit on all days. LightGBM needs at
least 30 incidents in the selection. Test-window daily MAE (flat / Bayes / LightGBM):
All Calgary 6.86 / 6.12 / 6.20; SE 2.76 / 2.56 / 2.51; Stoney Trail 1.29 / 1.28 / 1.12;
Deerfoot Trail 1.15 / 1.17 / 1.45; Collisions 2.48 / 2.33 / 2.68. No model wins everywhere.

### Original Bayes-only backtest

`backend/app/domain/forecast.py` forecasts the number of reported incidents for any
selection of area (quadrant), route, direction, lane, incident type or intersection.
Expected incidents per weekday × period are estimated from the selection's history,
shrunk toward the citywide weekly shape (4 pseudo-weeks), and treated as Poisson.
**Named baseline:** flat daily average over the same training days. Backtest:
train on the first 156 observed days, test on the last 28 (2026-09-04 → 10-02).

| Selection | History | Next 7 days (80% range) | Test actual / expected | Daily MAE model / baseline | vs baseline | 80% range hit rate |
|---|---:|---|---|---|---:|---:|
| All Calgary | 3,987 | 151.3 (136–167) | 625 / 596 | 6.12 / 6.86 | **10.7% better** | 60.7% |
| SE quadrant | 1,275 | 48.4 (40–57) | 177 / 196 | 2.56 / 2.76 | 7.1% better | 82.1% |
| Collisions only | 970 | 36.9 (29–45) | 147 / 146 | 2.33 / 2.48 | 6.1% better | 75.0% |
| Deerfoot Trail | 383 | 14.5 (10–20) | 43 / 61 | 1.17 / 1.15 | 1.3% worse | 85.7% |
| Deerfoot SB, right lane | 78 | 3.0 (1–5) | 10 / 12 | 0.60 / 0.58 | 4.1% worse | 96.4% |
| Deerfoot & Glenmore SE | 77 | 2.9 (1–5) | 8 / 12.5 | 0.48 / 0.48 | 1.3% worse | 100% |

Reading: weekday/time-of-day structure helps for large selections; for a single
route, lane or intersection the counts are too sparse to beat a plain average,
and the UI says so. Citywide the 80% range is too narrow (60.7% hit rate), i.e.
day-to-day variation exceeds Poisson. September Deerfoot incidents ran below the
earlier months. These are in-sample-period checks on one 28-day holdout, not a
validated operational forecast.

## Refresh and automation

```sh
make disruptions   # backfill into the database, then export this folder
make collect       # incremental poll (make collect-loop: every 5 minutes)
```

Backfill options: `--months N` (default 6), `--db PATH`, `--export-only`. The API and
MCP server pick up database changes automatically. Figures above describe the
October 3 build; the collector changes them as new data arrives.
