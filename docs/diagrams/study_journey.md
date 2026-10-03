# D-BB-JOURNEY-001 — Study and review handoff

Related: [engineer journey](../user_journeys/planner.md),
[reviewer journey](../user_journeys/budget_reviewer.md),
[stories](../user_stories/planning.md). Current professional workflow is a
hypothesis; green nodes represent the local prototype's executable slice.

```mermaid
flowchart TB
  subgraph Existing["Professional study workflow - hypothesis"]
    A["Agree corridor decision and objectives"] --> B["Collect model inputs and observations"]
    B --> C["Calibrate baseline and compare alternatives"]
    C --> D["Prepare recommendation and review evidence"]
    D --> E["Engineering review and authorized next step"]
  end
  subgraph Demo["Bottleneck Busters - working synthetic demonstrator"]
    P["Problem: inspect sources and assumptions"] --> I["Interventions: costs, budget, service limit"]
    I --> S["SUMO: propose, simulate, score, revise"]
    S --> R["Recommendation: options, exclusions, stress checks"]
    R --> X["Export scenario, trace and result evidence"]
  end
  B -. "Real baseline ingestion/calibration remains missing" .-> P
  X -. "Proposed reviewer handoff" .-> D
  E --> F["Further study or supervised field evaluation"]
  classDef local fill:#d9efe6,stroke:#27694c,color:#15251e
  class P,I,S,R,X local
```

The demo does not bypass calibration or engineering review. A JSON export is an
evidence handoff, not approval, funding allocation or a signal-control command.
