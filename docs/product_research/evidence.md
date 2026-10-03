# Evidence ledger and existing alternatives

Checked October 3, 2026. Source descriptions below are short paraphrases. Vendor
pages establish advertised capabilities, not independent performance benchmarks.
The reviewed alternatives are representative, not an exhaustive market survey.

## Primary sources

| ID | Source | Supported fact | Product implication — our interpretation |
|---|---|---|---|
| R1 | [Calgary: Traffic signal management](https://www.calgary.ca/roads/traffic-signal-management.html) | Calgary operates TransSuite, connects 1,300 signals to its Traffic Management Centre, and reports 70 coordinated corridors. Sensor volumes/speeds support operations. | The city already has expertise and operational infrastructure. Public access to those internal measurements is not established. |
| R2 | [Calgary: Vehicle data](https://www.calgary.ca/planning/transportation/data/vehicle.html) | CalTRACS provides intersection/road counts, vehicle classes, turning data and downloadable PDF/Excel reports. | Counts can support a study; selecting a relevant date/location is still necessary. |
| R3 | [CalTRACS help](https://trafficcounts.calgary.ca/Help/CalTRACSOnlineHelp.htm) | Consultants use the system for analysis/reporting; standard intersection studies record 15-minute increments and approach movements. | Preserve study provenance and movement definitions. Our two-rate importer is not a full CalTRACS or turning-count adapter. |
| R4 | [CalTRACS FAQ](https://www.calgary.ca/content/dam/www/transportation/tp/documents/data/caltracs-faq.pdf) | Counts are time-specific snapshots affected by conditions; raw data does not include analysis. | Neither a count nor an incident list alone measures an intervention's effect. |
| R5 | [Calgary: Corporate Asset Management](https://www.calgary.ca/our-services/asset-management.html) | CAMP links asset condition and risk to investment planning. It informs decisions; it does not approve projects or funding. | Maintenance prioritization and project approval are different jobs from a corridor traffic experiment. |
| R6 | [Roads & Pathways needs assessment, April 2026](https://www.calgary.ca/content/dam/www/is/capital-planning-business-services/documents/roads-pathways-10-year-captial-infrastructure-needs-assessment.pdf), pp. 2–5 | Calgary identifies aging assets, needs exceeding capital capacity, and renewal priorities based on condition, usage and network role. | Funding pressure is documented. It does not establish that our workflow solves a procurement or prioritization gap. |
| R7 | [Cubic: Synchro Studio](https://www.cubic.com/transportation/products/intelligent-transportation-solutions/intersection-optimization/synchro-studio) | Synchro/SimTraffic advertise signal optimization, microscopic simulation, scenario management and geometry/volume/timing comparison. | Optimization and scenario comparison are established capabilities; our novelty cannot rest on their mere existence. |
| R8 | [PTV: Vissim](https://www.ptvgroup.com/en-us/products/ptv-vissim) | Vissim advertises multimodal microsimulation, signal programs and scenario evaluation for planners, engineers and consultants. | Pedestrians/transit and richer network modeling are established alternatives and missing from our executable slice. |
| R9 | [FHWA: Model Calibration, March 2014](https://www.fhwa.dot.gov/publications/research/operations/13026/007.cfm); [current toolbox index](https://ops.fhwa.dot.gov/trafficanalysistools/toolbox.htm) | Calibration guidance compares modeled performance with field measurements and accounts for variability across days and random seeds. The toolbox lists a 2019 Volume III update. | Paired synthetic seeds test method behavior; field calibration is still required. This is methodological guidance, not Calgary policy or regulatory approval. |
| R10 | [SUMO documentation](https://sumo.dlr.de/docs/index.html) | SUMO documents network/demand inputs, count-based routing, simulation outputs and control interfaces. | Our simulator engine already exists. Product value must be demonstrated in orchestration, review and integration. |

The 2019 FHWA PDF could not be opened through the research browser. Its listing
was verified; detailed calibration statements above rely on the accessible 2014
chapter. No inaccessible document is represented as fully reviewed.

## Alternatives and the unresolved gap

| Alternative | Existing capability | What we need to investigate | Relationship to our prototype |
|---|---|---|---|
| Calgary operational signal system (R1) | Monitor/control signals and coordinate corridors | How are offline changes proposed, reviewed, and documented? | Potential future data/integration boundary; no connection today |
| CalTRACS (R2–R4) | Retrieve observed study data | Time spent selecting, interpreting and transforming studies | Data source, not a competing intervention lab |
| Synchro/SimTraffic (R7) | Optimize, simulate and compare scenarios | Can existing scenario/report workflows already solve the alleged pain? | Strong incumbent; no comparative benchmark or import/export integration yet |
| Vissim (R8) | Detailed multimodal simulation and evaluation | Existing scripting, review workflows, model ownership and switching costs | Strong incumbent; future adapter only if users require it |
| SUMO plus scripts (R10) | Programmable simulator and tooling | Would a small script provide the same value to the target user? | Direct low-cost alternative; also our underlying engine |
| Existing engineer study/report process | Case-specific professional judgment and deliverable preparation | Actual tools, handoffs, repeat work and decision deadlines | Current workflow must be observed; spreadsheet/email use is not assumed |

**We have not established that current solutions are insufficient.** The gap to
test is repeated work between validated model inputs, policy constraints,
outcome-based revision, and a reviewer-readable evidence package. Existing tools
may already cover it; a customer comparison must be allowed to disprove the idea.

## Claims register

| Claim | Status | Evidence or required test |
|---|---|---|
| Municipal investment has competing needs | Supported context | R6; not a measurement of software demand |
| Calgary has no engineering solution / chooses randomly | Unsupported; exclude | R1, R5 and R7–R8 contradict the blanket premise |
| Team has interviewed a domain practitioner | Unsupported; exclude | User clarified the family contact is outside the department |
| Agent workflow executes and revises a proposal | Implemented locally | [Planner code](../../backend/app/application/planner.py), [recorded trace](../demo/example_result.json) |
| Selected default revision reduces modeled delay by 27.17% | Recorded synthetic result | Same report; synthetic equal-green reference, three selection seeds |
| Workflow saves engineer/reviewer time | Untested customer hypothesis | Same-task comparison with existing workflow, including correction time |
| Costs reflect Calgary engineering estimates | Unsupported | Editable assumptions only; obtain scoped estimates |
| Product reduces Calgary congestion or improves safety | Not established | Observed baseline, missing modes/movements, engineering review, field evaluation |
| Municipality or consultant will pay | Untested commercial hypothesis | Identify budget owner, procurement route and a concrete pilot commitment |

## Two decisions we must keep separate

**Corridor operations:** whether a specified retiming or capacity alternative
improves modeled traffic performance under constraints. This matches the current
application's action space.

**Maintenance/capital portfolio:** which assets to renew, when, and with what
funding. This needs condition, failure consequences, lifecycle/delivery costs,
dependencies and service objectives. Delay alone cannot decide it; the prototype
does not solve this portfolio problem. Confirm which decision prospective users
actually struggle with before extending the product.
