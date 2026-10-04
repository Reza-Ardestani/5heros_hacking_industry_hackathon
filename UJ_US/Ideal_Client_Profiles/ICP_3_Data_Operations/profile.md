# ICP-BB-003 — External data and resource-evidence client

Status: proposed supporting workflow, not an implemented supplier integration or
validated buyer. [Journey UJ-BB-003](../../User_Journey_3/journey.md).

Primary user: a transportation data steward / integration analyst responsible for
source qualification, access permissions, mapping, freshness, and reproducibility.
Public-works scheduling, procurement, estimating, and contractor coordinators are
contributors to labor, materials, equipment, and work-window evidence.

Job: when a planner compares a physical intervention with an operational one, help
me provide attributable, time-bounded cost and resource evidence so feasibility
reflects what is actually available for the proposed location and work period.

Pains to validate: cost estimates disconnected from resource availability, rates
without scope or units, a forecast treated as a binding supplier commitment, and
manual repair of changed feed schemas. These are hypotheses requiring discovery.

Buyer: the same planning/consulting organization as UJ-1, unless research shows an
independent integration-product buyer. This supporting journey is not automatically
a third business line. Data stewards do not gain authority to approve construction.

Pilot fit: authorized City/internal planning data and at least one actual dated
quote or scheduling record with known ownership. Start with approved files/manual
evidence when no API exists; new sensors do not supply workforce or supplier facts.

Success measures: compatible sources identified, invalid mappings rejected,
duplicate polls replayed safely, freshness failures exposed, and past decisions
reproduced from their frozen evidence. No invented records or automatic external
supplier/organizer messages.
