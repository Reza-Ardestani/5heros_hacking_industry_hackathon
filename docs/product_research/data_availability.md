# Traffic data availability and decision readiness

Checked October 3, 2026. [Direct API probe evidence](data_api_probe.json) records
ten successful bounded requests, URLs, timestamps, payload fingerprints and
extracted schemas/samples. These are manual research probes, not an implemented
autonomous connector or database. An earlier whole-history aggregate query timed
out; no complete row count or earliest-date claim is made.

## Calgary: what exists, why it is collected, what it can support

| Data | Access verified or documented | Collection purpose | Decision coverage / remaining gap |
|---|---|---|---|
| Incident location, description, start/update times | Public Socrata JSON; [archive 35ra-9556](https://data.calgary.ca/d/35ra-9556) | Communicate disruptions and support traffic operations | Context/events; not vehicle counts, congestion severity or reliable clearance duration |
| Directional permanent-station counts | Public Socrata [vuyp-sbjp](https://data.calgary.ca/d/vuyp-sbjp), metadata/rows verified | Metadata identifies trend analysis and seasonal/weekly adjustment of short studies | Strong demand candidate. Sample/latest ordered rows dated Aug. 31, 2026; monthly publication. Count-bin duration, timezone and segment-to-network join still need confirmation |
| Intersection turns, classifications, pedestrian/cyclist counts and speed studies | [CalTRACS reports/help](https://trafficcounts.calgary.ca/Help/CalTRACSOnlineHelp.htm); PDF/Excel access documented, no selected workbook downloaded | Timing/warrant/operational studies and transport planning | Movement/mode-specific demand candidate; selected corridor/time coverage not established; full adapter absent |
| Daily average road volumes and line geometry | Public Socrata [2024 dataset cauu-7hnw](https://data.calgary.ca/d/cauu-7hnw); metadata/sample verified | Broad network demand/trend representation | Two-way daily average, not observed directional peak arrivals. Metadata text mentions 2023 despite title/sample year 2024: resolve conflict before combining years |
| Signal locations and accessibility inventory | Public Socrata [qr97-4jvx](https://data.calgary.ca/d/qr97-4jvx); schema/sample verified | Public inventory of City-maintained signals | Locate intersections/features; no phase sequence, cycle/split/offset or live controller state in sampled schema |
| Vehicle sensor volumes/speeds and signal state | [City describes TransSuite/TMC](https://www.calgary.ca/roads/traffic-signal-management.html) | Operate/monitor signals and provide transport/emergency priority | City already collects relevant operational data. Public machine-readable feed and access to internal history not established |
| Cameras, closures and drive-time information | [Traveller information](https://www.calgary.ca/roads/conditions.html); camera dataset found in catalog | Inform travelers and traffic operations | A public image or displayed drive time does not establish a historical, numeric, licensed API suitable for calibration |
| Cordon counts, mode shares and travel surveys | [Combined transport data](https://www.calgary.ca/planning/transportation/data/combined.html) | Understand travel trends and plan services/network | Broader planning context; aggregated surveys/mode shares cannot replace corridor observations |
| Active-mode counts | [Active transportation data](https://www.calgary.ca/planning/transportation/data/active-transportation.html) | Support walking/cycling planning | Check local movement/time coverage before claiming multimodal service protection |

Statements about purpose follow City descriptions; decision coverage is our
engineering interpretation. Neither catalog presence nor a recent download
certifies measurement quality, site coverage or suitability for an algorithm.

## What remains necessary for a defensible corridor comparison

Demand needs observed arrivals/turns by location, direction, mode and compatible
period. The network needs validated lanes, permitted movements, speeds and
connectivity. The baseline needs actual signal phases/timings and observed
queues/travel times for calibration. Intervention evaluation also needs approved
service constraints and scoped cost estimates. No public source set verified here
completes all of these requirements.

For live advice, add a fresh continuous feed, measured publication lag, outage
detection and relevant current network/signal state. The August monthly count
publication is usable historical material, not October live demand. Offline
planning and live advice can share the contract but cannot share freshness gates.
Neither profile authorizes real signal control.

## Ask for existing data before adding sensors

First request one complete, shareable corridor study and an explanation of the
permanent-count timestamp/bin semantics. Then request current/archived controller
timings, available detector history and observed travel-time/queue studies.
Coverage may exist internally even when a public API is absent. No City request
was sent by this research.

If gaps persist, propose a targeted manual turning/queue count, travel-time run,
or temporary collection using an approved method. New permanent sensors are a
later choice justified by the required cadence, coverage and collection cost;
they are not a prerequisite for the hackathon demonstrator. The agent can report
which measurement would unlock which decision; it cannot manufacture an observation.

## Other-city compatibility: three useful counterexamples

| City/source | Live probe result | Correct agent decision |
|---|---|---|
| Calgary permanent counts | Numeric volume, direction, segment/study IDs and floating timestamp | Conditional historical-demand candidate; resolve bins/timezone/location mapping and quality before promotion |
| Edmonton [AAWDT b58q-nxjr](https://data.edmonton.ca/d/b58q-nxjr) | Annual daily values; metadata allows actual and estimated values | Suitable for long-term-volume context; reject as measured peak-period arrivals |
| Edmonton [speed sign auch-8ddj](https://data.edmonton.ca/d/auch-8ddj) | Timestamped 15-minute speed bins and detector counts; metadata explicitly says counts must not be equated with traffic volume | Classify as speed/detection evidence; reject automatic conversion to full demand |
| Vancouver [intersection traffic movement counts](https://opendata.vancouver.ca/explore/dataset/intersection-traffic-movement-counts/) | API returns geometry, intersection name and report URL; 659 entries at probe time | Discover linked studies; catalog records alone fail the numeric movement-count contract |

This proves provider reachability and exposes semantic pitfalls, not fully
working cross-city integrations. Other cities demonstrate portability and can
support their own studies. Their counts are not Calgary ground truth. Deliberate
transfer/assumed-demand experiments must retain that label and separate provenance.

## Next slice

Build a bounded source-discovery/qualification loop before citywide optimization:
two generic providers, contract-based compatibility results, durable raw and
normalized batches, repeatable ingestion, quality quarantine, frozen dataset
versions for simulations. [Design](../design/data-federation/design.md),
[contract](../design/data-federation/data_contract.md),
[draft spec](../../specs/features/phase-2-data-federation/requirements.md).
