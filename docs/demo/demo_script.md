# Five-minute live demo — Bottleneck Busters

Run the API and UI before the pitch, check health and perform one real run. Keep
[recorded evidence](example_result.json) and four [screenshots](screenshots/) as an
explicitly labeled prior-run fallback; never imply they are a live result.

## Story and timing

1. **0:00–0:40 — Problem/user.** A transportation planner needs an auditable shortlist
   before spending scarce capital. Existing traffic engineering and simulation
   tools already exist; our hypothesis is faster preparation, revision and evidence
   packaging. We have not interviewed City staff or proven a staffing gap.
2. **0:40–1:15 — Evidence boundary.** Show the attributed Calgary incident snapshot.
   Incidents are disruptions, not traffic flow. Our executable corridor and arrivals
   are synthetic; measured-profile import is available, City flow calibration pending.
3. **1:15–2:20 — Act.** Advance from the problem to interventions. Set $100,000 budget and 30%
   cross-street delay guardrail. Choose Run simulation. Show SUMO vehicles, source assumptions and actual agent
   trace. Policy agents use simulator tools; no fake LLM conversation or trained RL.
4. **2:20–3:15 — Reason/revise.** Default demand-based plan favors the arterial too
   much and fails the cross-street constraint. Revision uses observed delay increase
   to reduce its signal change. Capacity improvement fails the assumed budget.
5. **3:15–4:00 — Evaluate.** Open Review recommendation. Show frozen alternatives on three paired seeds,
   Pareto cost-delay view, trip completion and ±20% demand checks. Recorded default:
   27.17% less modeled total delay, cross delay +14.80%, $15,000 estimated capital.
   Always read current results; edited demand may select another option or baseline.
6. **4:00–4:35 — Audit.** Download the real JSON report. Point to source hashes,
   per-seed results, assumptions, constraints and honest failures. Show architecture:
   React frontend, FastAPI orchestration, pure domain, SUMO infrastructure adapter.
7. **4:35–5:00 — Product/pilot.** Proposed customer: City/consultant planning teams.
   First pilot reproduces one observed corridor study before proposing a change.
   Monetization and willingness to pay are hypotheses, not signed customers.

## Q&A

- **Why no RL?** Weekend environment lacks calibrated ground truth and enough
  training/evaluation. Bounded simulator search provides inspectable action/revision.
  Later compare surrogate optimization or RL against this baseline fairly.
- **Is 27% a City saving?** No. Preliminary output of a labeled synthetic experiment.
  No observed Calgary signal/traffic baseline has been calibrated.
- **How do costs matter?** Hard capital constraint, cost-delay Pareto alternatives,
  optional occupancy/time-value annualization. All present costs are assumptions.
- **Could you remove lights/build ramps?** Those need pedestrian/safety/geometry and
  constructibility evidence. Current action space is split retiming and lane capacity.
- **Are these agents?** Deterministic policies call tools, score outcomes and revise.
  They are not LLMs. Organizer rubric permits optimizer/simulation/automated revision.
- **What changes for deployment?** Durable jobs/storage, authentication, resource
  isolation, job lifecycle, API hosting/proxy and operational validation.

## Submission preparation — open gates

Custom-case organizer acceptance, final captain/registration, actual form fields,
video/live-site link, final design package and final GitHub issue remain unverified.
Four authentic screenshots are captured locally, not submitted. Verify screenshots
and pitches contain no participant private data. Final submission deadline:
Sunday October 4, 2026 noon MDT. Do not push to organizer main.
