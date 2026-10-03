# Traffic data contract v1 — proposal

Status: design proposal, not implemented. Profiles: historical corridor planning
and live advisory evaluation. [Source assessment](../../product_research/data_availability.md).
Build typed validation from this contract; do not give the agent arbitrary SQL,
Python transformations or authority to invent measurement semantics.

## Shared envelope

Every record carries `contract_version`, `city_id`, `source_id`, `dataset_id`,
`source_record_id`, `record_revision`, `batch_id`, `retrieved_at_utc`, original
source timestamp/text, measurement method, observed/estimated/synthetic status,
quality flags and mapping version. Keep provenance through derived features.
Absence is explicit, not converted to zero. Original measurement times are
preserved; retrieval and publisher-update times are separate fields.

## Typed payloads

| Kind | Required semantics | Units and exclusions |
|---|---|---|
| `interval_count` | Study/site ID, segment or approach, direction/movement, mode/class, interval start/end, count, interval/timezone evidence | Integer vehicles/persons within known interval; no annual average or speed-detector subset disguised as complete traffic |
| `daily_volume` | Site, direction aggregation, year/date scope, averaging/seasonal method, actual-or-estimated declaration | Vehicles/day; not an interval count and cannot become peak flow merely by dividing by 24 |
| `speed_summary` | Site/direction, interval, unit, statistic/bins, detection population/limits, sample size if available | m/s internally, preserve source km/h or mph; detector selection bias flagged |
| `travel_time` | Route/direction, time interval, seconds, method, sample size if available | Route travel seconds; single-road speed is not a measured route time |
| `event` | Source event key, description/type, geometry/location, occurrence/update times and known status | Missing clearance is unknown; incident frequency is not demand |
| `network_inventory` | Stable local IDs, geometry/coordinate system, type, applicable attributes and effective/version dates | Signals/roads/lanes separately typed; coordinates do not establish connectivity or allowed movements |
| `signal_plan` | Junction, active period, phase/movement mapping, cycle, splits, offsets, clearance and pedestrian constraints | Seconds; inventory location is not an observed timing plan |
| `cost_estimate` | Action/site scope, currency, capital/operating components, date, method/assumptions and uncertainty | CAD for local decision; illustrative estimate distinct from scoped engineering quote |

Raw records can be stored without qualifying for these typed decision inputs.
Unknown interval boundaries/timezone keep a count candidate quarantined from
simulation-ready demand. Turning and approach direction differ; keep both where
available. City-local IDs require an explicit network crosswalk with evidence.

## Derived demand interface

`get_demand(city_id, network_version, location_set, time_window, profile)` returns
movement-specific rates/vehicle classes, provenance, missing coverage, quality
and immutable dataset version. For a confirmed count, rate equals
`count * 3600 / interval_seconds`; a 15-minute count is multiplied by four.
This conversion does not infer missing turns, other directions or weekdays.

The current simulator consumes symmetric two-rate arrivals shared across three
junctions. A new demand adapter must preserve per-site/direction/movement data or
explicitly declare aggregation assumptions. Do not label that existing importer
as a complete movement/network interface.

## Decision readiness profiles

| Gate | Historical corridor planning | Live advice |
|---|---|---|
| Time suitability | Date, season, weekday and peak period relevant to the chosen study; maximum age explicit | Latest measurement and publication lag within configured SLA; illustrative starting target <=5 minutes, not a City standard |
| Completeness | Required locations/movements covered; gaps surfaced | Coverage plus uninterrupted recent intervals; outage/stale status required |
| Model evidence | Geometry, observed timings and independently reviewed baseline observations | Same model requirements plus relevant current network/signal state |
| Missing data outcome | Return partial evidence/missing-data request; assumption-based runs labeled | Withhold current-data recommendation; show stale/insufficient evidence |

Readiness results: `compatible`, `conditional`, `incompatible`, `unavailable`,
`unsupported_format`. Include reasons, evidence references and missing fields.
Readiness is per task/profile, not a permanent stamp attached to a whole city.
Finite numeric checks and timestamp/unit validation are deterministic gates;
model confidence or an LLM's confidence cannot bypass them.

## Connector manifest

Agent-produced configuration contains provider family, approved public domain,
dataset ID, schema fingerprint, record key, typed field mappings, evidence for
units/timezone/bin semantics, allowed transform names, pagination strategy,
update/deletion capability, polling cadence and role restrictions. Example:

```json
{
  "provider": "socrata",
  "city_id": "calgary",
  "domain": "data.calgary.ca",
  "dataset_id": "vuyp-sbjp",
  "target_kind": "interval_count",
  "mapping": {"count": "volume", "direction": "direction", "location_id": "segment_id", "raw_timestamp": "study_date", "source_record_id": "id"},
  "interval_seconds": null,
  "timezone": null,
  "readiness": "conditional",
  "missing": ["confirmed interval/timezone semantics", "segment-to-network crosswalk"],
  "publisher_update_frequency": "Monthly"
}
```

This is a proposal from sampled metadata, not an active connector. Unknown
semantics remain null until supported. Manifest versions are immutable after
activation; schema drift triggers qualification of a new mapping version.
