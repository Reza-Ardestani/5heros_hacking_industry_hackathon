# UJ-BB-003 — Qualify city data for a decision

Proposed journey, October 3, 2026; not implemented. Actor: transportation analyst
choosing a city, corridor/time window, and historical-study or live-advice profile.
No new user interview is claimed. [Contract](../design/data-federation/data_contract.md),
[design](../design/data-federation/design.md).

| Stage | Current boundary | Proposed experience | Success / failure evidence |
|---|---|---|---|
| State need | Developer selects incident source; analyst normalizes demand JSON | Analyst states city/task and required measurements | Task profile and readiness gates visible |
| Discover | Manual catalog search and schema investigation | Agent searches provider catalogs and samples candidates | Source URL/schema/sample and reason for each choice |
| Qualify | Source names may overstate usable content | Agent tests fields, units, intervals, location/time coverage and freshness | Compatible/conditional/rejected result with exact gaps |
| Configure | New integrations require adapter knowledge | Agent emits a validated manifest for supported provider | Mapping revision tested; unsupported format remains explicit |
| Ingest | Snapshot refresh; no normalized durable DB | Trusted core fetches, persists, deduplicates and resumes | Raw batch, revisions, quality and checkpoint auditable |
| Use | Simulation uses synthetic/default or user-supplied arrivals | Engine consumes qualified frozen data version | Model readiness still required; no automatic field-benefit claim |
| Repair / collect | Developer investigates failed or missing source | Agent chooses permitted repair/alternative or drafts measurement request | No invented values; no external message sent automatically |

Live and historical readiness can differ for the same stored source. A source
passing the storage/schema contract does not automatically qualify for either
simulation profile. Related [stories F-BB-4–6](../user_stories/planning.md).
