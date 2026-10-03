# D-BB-DATA-001 — Proposed autonomous data pipeline

[Design](../design/data-federation/design.md),
[journey](../user_journeys/data_onboarding.md). All new ingestion components
below are proposed; existing SUMO workflow is separate implemented evidence.

```mermaid
flowchart LR
  Need["City + task profile + data contract"] --> Agent["Discover and qualify sources"]
  Catalog["City catalogs / metadata / samples"] --> Agent
  Agent --> Config["Typed connector manifest"]
  Config --> Core["Shared adapters + fetch / retry / checkpoint"]
  Poll["Scheduler; provider webhook only if supported"] --> Core
  Core --> Raw["Durable raw batches"]
  Raw --> Validate["Normalize + semantic / quality gates"]
  Validate --> DB["Revisioned normalized storage"]
  Validate -. "Rejected batch and evidence" .-> Agent
  Agent --> Gaps["Exact missing-data request"]
  DB --> Ready["Historical / live readiness gates"]
  Ready --> Version["Freeze dataset version"]
  Version --> Model["Model validation + SUMO decision loop"]
  Ready -. "Stale or missing measurements" .-> Gaps
```

Shared ingestion infrastructure supports both profiles. Historical counts cannot
pass live freshness gates by being fetched again. Other-city data remains isolated
by city/location identity and measurement provenance.
