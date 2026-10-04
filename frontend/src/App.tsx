import React, { useEffect, useState } from "react";
import {
  ArrowUpRight,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Download,
  FileText,
  FlaskConical,
  GitBranch,
  Info,
  Loader2,
  MapPin,
  Pause,
  Play,
  RotateCcw,
  Route,
  Settings2,
  ShieldCheck,
  TrafficCone,
  Wallet,
  X,
} from "lucide-react";

import type { Scenario, Incidents, IntersectionStudy, Job, View } from "./types";
import { kindNote, money, number, names, optionName } from "./lib/format";
import { request } from "./lib/api";
import {
  Stat,
  Decision,
  EmptyState,
  Network,
  CostChart,
} from "./components/StudyComponents";
import { IntersectionExplorer } from "./components/IntersectionExplorer";
import { SettingsAdvisor, SimulationLog } from "./components/DecisionExplain";
import {
  EvidenceSummaryPanel,
  StudyBanner,
  StudyDesign,
  TestPlan,
  defaultStudyFields,
} from "./components/StudyDesign";

const defaults: Scenario = {
  main_vph: 1050,
  cross_vph: 160,
  duration_s: 900,
  seed: 42,
  budget_cad: 100000,
  cross_guardrail_pct: 30,
  retiming_cost_cad: 15000,
  widening_cost_cad: 1200000,
  annual_operating_cost_cad: 2000,
  occupancy: 1.2,
  value_of_time_cad: 20,
  operating_days: 250,
  asset_life_years: 10,
  demand_kind: "synthetic",
  demand_source: "Synthetic directional arrivals; not CalTRACS",
  flow_profile: null,
  ...defaultStudyFields,
};
export default function App() {
  const [scenario, setScenario] = useState<Scenario>(defaults),
    [incidents, setIncidents] = useState<Incidents | null>(null),
    [study, setStudy] = useState<IntersectionStudy | null>(null),
    [job, setJob] = useState<Job | null>(null);
  const [view, setView] = useState<View>("problem"),
    [step, setStep] = useState(1),
    [error, setError] = useState(""),
    [selected, setSelected] = useState("reference"),
    [frame, setFrame] = useState(0),
    [playing, setPlaying] = useState(false),
    [advanced, setAdvanced] = useState(false);
  const result = job?.result,
    reference = result?.alternatives[0],
    recommendation = result?.alternatives.find(
      (a) => a.id === result.recommended_id,
    ),
    active = result?.alternatives.find((a) => a.id === selected);
  const busy = job?.status === "running",
    frames = active?.tuning_trial.playback ?? [],
    current = frames[Math.min(frame, Math.max(0, frames.length - 1))];
  const go = (next: number) => {
    setStep(next);
    setView(next === 1 ? "problem" : next === 4 ? "compare" : "study");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const changed =
    !!result && JSON.stringify(scenario) !== JSON.stringify(result.scenario);
  const averageFlow = (key: "main_vph" | "cross_vph") =>
    scenario.flow_profile
      ? scenario.flow_profile.reduce(
          (total, i) => total + (i.end_s - i.begin_s) * i[key],
          0,
        ) / scenario.duration_s
      : scenario[key];
  useEffect(() => {
    request<{ defaults: Scenario }>("/api/scenario")
      .then((v) => setScenario(v.defaults))
      .catch((e) => setError(e.message));
    request<Incidents>("/api/incidents")
      .then(setIncidents)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (!job?.id || job.status !== "running") return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const next = await request<Job>(`/api/jobs/${job.id}`);
        if (stopped) return;
        setJob(next);
        if (next.status === "completed") {
          setSelected(next.result?.recommended_id ?? "reference");
          setFrame(30);
          setPlaying(false);
        }
        if (next.status === "running") timer = setTimeout(poll, 900);
        if (next.status === "failed")
          setError(next.error ?? "Simulation failed");
      } catch (e) {
        if (!stopped) {
          setError((e as Error).message);
          timer = setTimeout(poll, 2000);
        }
      }
    };
    timer = setTimeout(poll, 500);
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [job?.id, job?.status]);
  useEffect(() => {
    if (!playing || !frames.length) return;
    const timer = setInterval(
      () => setFrame((v) => (v + 1) % frames.length),
      180,
    );
    return () => clearInterval(timer);
  }, [playing, frames.length]);
  const change = (key: keyof Scenario, value: number) =>
    setScenario((s) => ({ ...s, [key]: value }));
  async function start() {
    setError("");
    setPlaying(false);
    try {
      const query = study
        ? `?origin=intersection&intersection_key=${encodeURIComponent(study.intersection_key)}`
        : "";
      const next = await request<{ id: string }>(`/api/jobs${query}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(scenario),
      });
      setJob({
        id: next.id,
        status: "running",
        trace: [],
        result: null,
        error: null,
      });
      setSelected("reference");
      go(3);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function importProfile(file: File | undefined) {
    if (!file) return;
    try {
      const profile = JSON.parse(await file.text());
      if (
        !Array.isArray(profile.flow_profile) ||
        !profile.flow_profile.length ||
        typeof profile.demand_source !== "string" ||
        !profile.demand_source.trim() ||
        !Number.isInteger(profile.duration_s)
      )
        throw new Error(
          "Use flow_profile, demand_source and duration_s. Format documented in data/README.md.",
        );
      let end = 0;
      for (const i of profile.flow_profile) {
        if (
          !Number.isInteger(i.begin_s) ||
          !Number.isInteger(i.end_s) ||
          i.begin_s !== end ||
          i.end_s <= i.begin_s ||
          !Number.isFinite(i.main_vph) ||
          !Number.isFinite(i.cross_vph) ||
          i.main_vph < 0 ||
          i.cross_vph < 0
        )
          throw new Error(
            "Intervals must be contiguous, ordered and contain finite nonnegative arrivals.",
          );
        end = i.end_s;
      }
      if (end !== profile.duration_s)
        throw new Error("Intervals must cover duration_s exactly.");
      setScenario((s) => ({
        ...s,
        demand_kind: "measured",
        flow_profile: profile.flow_profile,
        demand_source: profile.demand_source,
        duration_s: profile.duration_s,
      }));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  const exportLink = (
    <a
      className={`button secondary ${!result ? "disabled" : ""}`}
      aria-disabled={!result}
      href={result ? `/api/jobs/${job!.id}/report` : "#"}
      download
      onClick={(e) => {
        if (!result) e.preventDefault();
      }}
    >
      <Download size={16} />
      Export report
    </a>
  );
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            go(1);
          }}
        >
          <span className="brand-icon">
            <Route size={22} />
          </span>
          <span>
            Bottleneck
            <br />
            <strong>Busters</strong>
          </span>
        </a>
        <div className="sidebar-caption">PLANNING WORKSPACE</div>
        <nav>
          {(
            [
              ["problem", FlaskConical, "Guided study", "01"],
              ["compare", GitBranch, "Compare options", "02"],
              ["intersections", TrafficCone, "Intersections", "03"],
              ["evidence", FileText, "Evidence & sources", "04"],
            ] as const
          ).map(([id, Icon, label, index]) => (
            <button
              className={
                view === id || (id === "problem" && view === "study")
                  ? "selected"
                  : ""
              }
              aria-label={label}
              onClick={() =>
                id === "problem"
                  ? go(1)
                  : id === "compare"
                    ? go(4)
                    : setView(id)
              }
              key={id}
            >
              <Icon size={18} />
              <span>{label}</span>
              <small>{index}</small>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="status-dot" /> Local prototype
          <div>Calgary · Hackathon 2026</div>
          <p>Plan. Test. Revise.</p>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <div className="breadcrumbs">
            Workspace <ChevronRight size={14} />{" "}
            <strong>
              {view === "evidence"
                ? "Evidence & sources"
                : view === "intersections"
                  ? "Intersection explorer"
                  : `Step ${step} of 4`}
            </strong>
          </div>
          <div className="topbar-meta">
            <span className="badge neutral">STUDY 001</span>
            <span className="avatar">BB</span>
          </div>
        </header>
        <div className="page-body">
          {view !== "evidence" && view !== "intersections" && (
            <div className="wizard-progress" aria-label="Study progress">
              {[
                "Frame the problem",
                "Choose interventions",
                "Run simulation",
                "Review recommendation",
              ].map((label, i) => (
                <button
                  key={label}
                  className={
                    step === i + 1 ? "current" : step > i + 1 ? "done" : ""
                  }
                  aria-current={step === i + 1 ? "step" : undefined}
                  disabled={(i === 2 && !job) || (i === 3 && !result)}
                  onClick={() => go(i + 1)}
                >
                  <span>{step > i + 1 ? <Check size={13} /> : i + 1}</span>
                  <strong>{label}</strong>
                </button>
              ))}
            </div>
          )}
          <section className="page-heading">
            <div>
              <div className="eyebrow">CALGARY / TRANSPORTATION PLANNING</div>
              <h1>
                {view === "problem"
                  ? "Which change earns its cost?"
                  : view === "study"
                    ? step === 2
                      ? "Define the changes worth testing."
                      : "Let the evidence decide."
                    : view === "compare"
                      ? "A recommendation you can inspect."
                      : view === "intersections"
                        ? "Where does traffic keep getting stuck?"
                        : "Show your working."}
              </h1>
              <p>
                {view === "problem"
                  ? "A guided corridor study for better traffic flow, within budget constraints."
                  : view === "study"
                    ? step === 2
                      ? "Set demand, spending limits and the cross-street protection rule."
                      : "Watch agents test, reject, revise and evaluate traffic interventions."
                    : view === "compare"
                      ? "Compare the whole corridor, the tradeoffs and the investment required."
                      : view === "intersections"
                        ? "Six months of City-reported incidents and closures by intersection, with the live City feed and cameras. Use it to choose which corridor to study."
                        : "Trace each decision back to inputs, assumptions and actual simulator output."}
              </p>
            </div>
            <div className="heading-actions">
              {result && exportLink}
              {view === "evidence" && (
                <button className="button primary" onClick={() => go(2)}>
                  <Settings2 size={16} />
                  Edit study
                </button>
              )}
            </div>
          </section>
          {error && (
            <div className="notice error" role="alert">
              <Info size={18} />
              <span>{error}</span>
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {changed && (
            <div className="notice warning">
              <Info size={17} />
              <span>
                Inputs changed. Results still describe the previous run. Run
                again to update the comparison.
              </span>
            </div>
          )}
          {view === "intersections" && (
            <IntersectionExplorer
              onStudy={(built: IntersectionStudy) => {
                setStudy(built);
                setScenario(built.scenario);
                go(2);
              }}
            />
          )}
          {view === "problem" && (
            <>
              <section className="problem-hero panel">
                <div className="problem-story">
                  <span className="badge blue">THE PLANNING QUESTION</span>
                  <h2>
                    Traffic backs up.
                    <br />
                    What should the city change?
                  </h2>
                  <p>
                    A transportation planner must choose between adjusting
                    signals and adding road capacity. Both may help the
                    arterial. Both carry tradeoffs.
                  </p>
                  <div className="problem-goal">
                    <ShieldCheck size={20} />
                    <div>
                      <strong>
                        Reduce corridor delay. Protect cross streets. Stay
                        within budget.
                      </strong>
                      <span>Our decision rule for this study.</span>
                    </div>
                  </div>
                  <button className="button primary" onClick={() => go(2)}>
                    Define the interventions <ArrowUpRight size={17} />
                  </button>
                  <span className="problem-duration">
                    Four steps · one reproducible experiment
                  </span>
                </div>
                <div className="problem-illustration">
                  <div className="illustration-caption">
                    A DECISION, BEFORE AN INVESTMENT
                  </div>
                  <div className="problem-road">
                    <i />
                    <i />
                    <i />
                    {Array.from({ length: 12 }, (_, i) => (
                      <span
                        key={i}
                        style={{
                          left: `${16 + i * 5.5}%`,
                          top: i % 2 === 0 ? "44%" : "56%",
                        }}
                      />
                    ))}
                  </div>
                  <div className="illustration-label">
                    <Clock3 size={18} />
                    <span>
                      Where does delay move
                      <br />
                      when we change a signal?
                    </span>
                  </div>
                  <div className="illustration-cost">
                    <Wallet size={20} />
                    <strong>Benefit × cost</strong>
                    <span>Test the tradeoff first.</span>
                  </div>
                </div>
              </section>
              <div className="problem-cards">
                <article className="panel">
                  <span className="small-step">01 / WHO</span>
                  <h3>City transportation planner</h3>
                  <p>
                    Prepare a reviewable investment shortlist for an engineer or
                    capital budget reviewer.
                  </p>
                </article>
                <article className="panel">
                  <span className="small-step">02 / TODAY</span>
                  <h3>Manual scenario comparison</h3>
                  <p>
                    Gather counts, configure models, compare options and explain
                    tradeoffs. Workflow pain remains a hypothesis to validate.
                  </p>
                </article>
                <article className="panel">
                  <span className="small-step">03 / WITH THE LAB</span>
                  <h3>A repeatable planning loop</h3>
                  <p>
                    Agents propose, simulate, measure and revise. Every option
                    includes constraints, costs and an auditable report.
                  </p>
                </article>
              </div>
              <section className="problem-scope panel">
                <div>
                  <MapPin size={21} />
                  <div>
                    <strong>Start small: three junctions, one corridor.</strong>
                    <p>
                      This early demo uses synthetic geometry and arrivals.
                      Calgary incident data supplies context; measured flow
                      calibration comes next.
                    </p>
                  </div>
                </div>
                <button
                  className="text-link"
                  onClick={() => setView("evidence")}
                >
                  Inspect data readiness <ArrowUpRight size={15} />
                </button>
              </section>
            </>
          )}
          {view === "study" && (
            <>
              <div className="study-context">
                <div>
                  <MapPin size={17} />
                  <strong>Three-junction demo corridor</strong>
                  <span>1.6 km arterial</span>
                </div>
                <span className="badge amber">
                  Synthetic geometry ·{" "}
                  {scenario.demand_kind === "synthetic"
                    ? "assumed arrivals"
                    : "imported arrivals"}
                </span>
                <button onClick={() => setView("evidence")}>
                  Check data readiness <ArrowUpRight size={14} />
                </button>
              </div>
              {study && (
                <StudyBanner
                  study={study}
                  onClear={() => {
                    setStudy(null);
                    setScenario(defaults);
                  }}
                />
              )}
              <div className="study-layout">
                <section className="panel setup">
                  <div className="panel-heading">
                    <h2>
                      {step === 3 ? "Experiment inputs" : "Set study limits"}
                    </h2>
                    <Settings2 size={18} />
                  </div>
                  <p className="helper">
                    {step === 3
                      ? "Review or edit inputs, then rerun."
                      : "What can the city spend? What must stay protected?"}
                  </p>
                  <label className="field-label" htmlFor="budget">
                    Capital budget
                  </label>
                  <div className="number-input">
                    <span>CAD</span>
                    <input
                      id="budget"
                      aria-label="Capital budget"
                      type="number"
                      min="0"
                      max="10000000"
                      step="5000"
                      disabled={busy}
                      value={scenario.budget_cad}
                      onChange={(e) => change("budget_cad", +e.target.value)}
                    />
                  </div>
                  <div className="flow-field">
                    <label htmlFor="main-flow">
                      Arterial arrivals{" "}
                      <strong>{number(averageFlow("main_vph"))}</strong>
                    </label>
                    <div className="unit">vehicles / hour / direction</div>
                    <input
                      id="main-flow"
                      type="range"
                      min="50"
                      max="1800"
                      step="25"
                      disabled={busy || scenario.demand_kind === "measured"}
                      value={averageFlow("main_vph")}
                      onChange={(e) => change("main_vph", +e.target.value)}
                    />
                    <div className="range-ends">
                      <span>50</span>
                      <span>1,800</span>
                    </div>
                  </div>
                  <div className="flow-field">
                    <label htmlFor="cross-flow">
                      Cross-street arrivals{" "}
                      <strong>{number(averageFlow("cross_vph"))}</strong>
                    </label>
                    <div className="unit">
                      vehicles / hour / direction / junction
                    </div>
                    <input
                      id="cross-flow"
                      type="range"
                      min="20"
                      max="600"
                      step="10"
                      disabled={busy || scenario.demand_kind === "measured"}
                      value={averageFlow("cross_vph")}
                      onChange={(e) => change("cross_vph", +e.target.value)}
                    />
                    <div className="range-ends">
                      <span>20</span>
                      <span>600</span>
                    </div>
                  </div>
                  <label className="field-label" htmlFor="guardrail">
                    Protect cross-street travel
                  </label>
                  <div className="number-input">
                    <input
                      id="guardrail"
                      aria-label="Cross-street delay guardrail"
                      type="number"
                      min="0"
                      max="200"
                      disabled={busy}
                      value={scenario.cross_guardrail_pct}
                      onChange={(e) =>
                        change("cross_guardrail_pct", +e.target.value)
                      }
                    />
                    <span>% max. delay increase</span>
                  </div>
                  <p className="helper guardrail-help">
                    Plans exceeding this limit are rejected.
                  </p>
                  <StudyDesign
                    scenario={scenario}
                    disabled={busy}
                    onChange={(patch) => setScenario((s) => ({ ...s, ...patch }))}
                  />
                  <button
                    className="disclosure"
                    aria-expanded={advanced}
                    onClick={() => setAdvanced(!advanced)}
                  >
                    Costs & assumptions{" "}
                    <ChevronRight
                      size={16}
                      className={advanced ? "rotated" : ""}
                    />
                  </button>
                  {advanced && (
                    <div className="advanced-grid">
                      {(
                        [
                          ["retiming_cost_cad", "Signal retiming · CAD"],
                          ["widening_cost_cad", "Extra lane · CAD"],
                          [
                            "annual_operating_cost_cad",
                            "Annual operations · CAD",
                          ],
                          ["occupancy", "People per vehicle"],
                          ["value_of_time_cad", "CAD per person-hour"],
                          ["operating_days", "Study days per year"],
                          ["asset_life_years", "Asset life · years"],
                          ["signal_install_cost_cad", "Add signal · CAD"],
                          ["signal_removal_cost_cad", "Remove signal · CAD"],
                          ["clearance_program_cost_cad", "Clearance program · CAD"],
                          ["turn_lane_cost_cad", "Left-turn bay · CAD"],
                          ["turn_ban_cost_cad", "Turn ban · CAD"],
                          ["seed", "Proposal seed"],
                          ["duration_s", "Arrival window · seconds"],
                        ] as [keyof Scenario, string][]
                      ).map(([key, label]) => (
                        <label key={key}>
                          {label}
                          <input
                            aria-label={label}
                            type="number"
                            disabled={busy}
                            value={scenario[key] as number}
                            onChange={(e) => change(key, +e.target.value)}
                          />
                        </label>
                      ))}
                    </div>
                  )}
                  <button
                    className="button primary run-button"
                    onClick={start}
                    disabled={busy}
                  >
                    {busy ? (
                      <>
                        <Loader2 size={18} className="spinner" />
                        Running simulation…
                      </>
                    ) : (
                      <>
                        <Play size={17} fill="currentColor" />
                        {result ? "Run updated study" : "Run simulation"}
                      </>
                    )}
                  </button>
                  <div className="run-note">
                    {4 + scenario.extra_options.length} options · 3 evaluation seeds
                    {scenario.incident && scenario.incident_weight < 1
                      ? " × 2 conditions"
                      : ""}{" "}
                    · 2 stress checks
                  </div>
                </section>
                <div className="experiment-column">
                  {step === 2 && (
                    <SettingsAdvisor
                      scenario={scenario}
                      result={result}
                      onApply={change}
                      disabled={busy}
                    />
                  )}
                  {step === 2 && <TestPlan scenario={scenario} />}
                  {step === 3 && (
                    <section className="panel network-panel">
                      <div className="panel-heading">
                        <div>
                          <h2>Corridor simulation</h2>
                          <p className="helper">
                            {active
                              ? names[active.id]
                              : "Your experiment starts here"}
                          </p>
                        </div>
                        <span className={`badge ${busy ? "blue" : "neutral"}`}>
                          {busy
                            ? "RUNNING"
                            : result
                              ? "COMPLETED"
                              : "READY TO RUN"}
                        </span>
                      </div>
                      <div
                        className="scenario-tabs"
                        aria-label="Playback alternative"
                      >
                        {(
                          result?.alternatives.map((a) => a.id) ?? [
                            "reference",
                            "candidate",
                            "revised",
                            "capacity",
                          ]
                        ).map(
                          (id) => (
                            <button
                              key={id}
                              disabled={!result}
                              className={selected === id ? "active" : ""}
                              onClick={() => {
                                setSelected(id);
                                setFrame(30);
                                setPlaying(false);
                              }}
                            >
                              {optionName(
                                id,
                                result?.alternatives.find((a) => a.id === id)?.label,
                              )}
                              {result?.recommended_id === id && (
                                <Check size={14} />
                              )}
                            </button>
                          ),
                        )}
                      </div>
                      <Network current={current} active={active} />
                      <div className="playback-controls">
                        <button
                          aria-label={
                            playing ? "Pause playback" : "Play playback"
                          }
                          disabled={!frames.length}
                          onClick={() => setPlaying(!playing)}
                        >
                          {playing ? <Pause size={17} /> : <Play size={17} />}
                        </button>
                        <button
                          aria-label="Restart playback"
                          disabled={!frames.length}
                          onClick={() => setFrame(0)}
                        >
                          <RotateCcw size={16} />
                        </button>
                        <input
                          aria-label="Simulation playback time"
                          type="range"
                          min="0"
                          max={Math.max(1, frames.length - 1)}
                          value={Math.min(
                            frame,
                            Math.max(0, frames.length - 1),
                          )}
                          disabled={!frames.length}
                          onChange={(e) => {
                            setPlaying(false);
                            setFrame(+e.target.value);
                          }}
                        />
                        <span>
                          {current
                            ? `${Math.floor(current.time_s / 60)}:${String(Math.round(current.time_s % 60)).padStart(2, "0")}`
                            : "00:00"}
                        </span>
                      </div>
                      <div className="playback-caption">
                        Actual SUMO positions · proposal seed · 10-second
                        samples · up to 150 vehicles
                      </div>
                    </section>
                  )}
                  {busy ? (
                    <section className="panel running-panel">
                      <Loader2 className="spinner" size={24} />
                      <div>
                        <h3>
                          {job?.trace.at(-1)?.agent ?? "Preparing experiment"}
                        </h3>
                        <p>
                          {job?.trace.at(-1)?.detail ??
                            "The simulator is preparing paired traffic inputs."}
                        </p>
                        <span>
                          {job?.trace.length ?? 0} recorded actions · results
                          appear after evaluation
                        </span>
                      </div>
                    </section>
                  ) : recommendation && reference ? (
                    <>
                      <Decision
                        result={result!}
                        recommendation={recommendation}
                        reference={reference}
                        onCompare={() => go(4)}
                      />
                      <div className="study-stats">
                        <Stat
                          icon={<Clock3 size={17} />}
                          label="Average vehicle delay"
                          value={`${number(recommendation.metrics.mean_delay_s)}s`}
                          note={`${number(reference.metrics.mean_delay_s)}s in reference plan`}
                        />
                        <Stat
                          icon={<Wallet size={17} />}
                          label="Estimated capital"
                          value={money(recommendation.capital_cost_cad)}
                          note={`Budget ${money(result!.scenario.budget_cad)}`}
                        />
                        <Stat
                          icon={<ShieldCheck size={17} />}
                          label="Cross-street change"
                          value={`${number(recommendation.comparison.cross_delay_change_pct)}%`}
                          note={`Limit ${result!.scenario.cross_guardrail_pct}% increase`}
                        />
                      </div>
                      {step === 3 && result && <EvidenceSummaryPanel result={result} />}
                      {step === 3 && job && <SimulationLog job={job} />}
                    </>
                  ) : (
                    <section className="panel start-guide">
                      <span className="step-circle">1</span>
                      <div>
                        <h3>Build an evidence-backed shortlist.</h3>
                        <p>
                          Set your limits, then run. Agents test a first
                          proposal, revise it from observed delay and compare
                          all options on identical arrivals.
                        </p>
                        <div className="guide-steps">
                          <span>Set limits</span>
                          <ChevronRight size={14} />
                          <span>Run & revise</span>
                          <ChevronRight size={14} />
                          <span>Compare costs</span>
                        </div>
                      </div>
                    </section>
                  )}
                </div>
              </div>
              <section className="data-strip">
                <div>
                  <Info size={17} />
                  <span>
                    <strong>Demo evidence boundary</strong> Calgary incidents
                    are real. This corridor and default arrivals are synthetic;
                    no Calgary field benefit has been verified.
                  </span>
                </div>
                <button onClick={() => setView("evidence")}>
                  View sources <ArrowUpRight size={15} />
                </button>
              </section>
            </>
          )}
          {view === "compare" &&
            (result && recommendation && reference ? (
              <>
                <Decision
                  result={result}
                  recommendation={recommendation}
                  reference={reference}
                />
                <div className="comparison-cards">
                  {result.alternatives.map((a) => (
                    <button
                      key={a.id}
                      className={`option-card ${a.id === selected ? "focused" : ""} ${a.id === recommendation.id ? "recommended" : ""}`}
                      onClick={() => setSelected(a.id)}
                    >
                      <div>
                        <span className="option-title">
                          {optionName(a.id, a.label)}
                        </span>
                        <span className="option-badges">
                          <span
                            className={`badge ${a.id === recommendation.id ? "green" : a.comparison.feasible ? "neutral" : "amber"}`}
                          >
                            {a.id === recommendation.id
                              ? "RECOMMENDED"
                              : a.comparison.feasible
                                ? "FEASIBLE"
                                : "REJECTED"}
                          </span>
                          {result.decision?.lowest_delay_id === a.id && (
                            <span className="badge blue">LOWEST DELAY</span>
                          )}
                        </span>
                      </div>
                      <strong>
                        {number(a.metrics.mean_delay_s)}
                        <small> s delay / vehicle</small>
                      </strong>
                      <span className="option-cost">
                        {money(a.capital_cost_cad)} estimated capital
                      </span>
                      <p>
                        {a.id === "reference"
                          ? a.label
                          : a.id === "capacity"
                            ? `${a.main_lanes} arterial lanes per direction`
                            : a.kind && kindNote[a.kind]
                              ? kindNote[a.kind]
                              : `${Math.round(a.main_green_share * 100)}% of usable green to arterial`}
                      </p>
                      {!a.comparison.feasible && (
                        <span className="option-reason">
                          {(a.comparison.rejection_details ?? [])
                            .map((d) => d.message)
                            .join(" · ") || a.comparison.rejection_reasons.join(" · ")}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
                <EvidenceSummaryPanel result={result} />
                <div className="compare-layout">
                  <section className="panel comparison-detail">
                    <div className="panel-heading">
                      <h2>
                        {optionName(active?.id ?? "reference", active?.label)} versus
                        reference plan
                      </h2>
                      <span className="helper">3 paired seeds · means</span>
                    </div>
                    {active && (
                      <>
                        <div className="comparison-bars">
                          {(
                            [
                              [
                                "Arterial delay",
                                reference.metrics.main_mean_delay_s,
                                active.metrics.main_mean_delay_s,
                              ],
                              [
                                "Cross-street delay",
                                reference.metrics.cross_mean_delay_s,
                                active.metrics.cross_mean_delay_s,
                              ],
                              [
                                "Overall vehicle delay",
                                reference.metrics.mean_delay_s,
                                active.metrics.mean_delay_s,
                              ],
                            ] as [string, number, number][]
                          ).map(([label, base, next]) => (
                            <div className="bar-pair" key={label}>
                              <h3>{label}</h3>
                              <div>
                                <span>Reference</span>
                                <i
                                  style={{
                                    width: `${(base / Math.max(base, next, 1)) * 62}%`,
                                  }}
                                />
                                <strong>{number(base)}s</strong>
                              </div>
                              <div>
                                <span>Option</span>
                                <i
                                  className="option-bar"
                                  style={{
                                    width: `${(next / Math.max(base, next, 1)) * 62}%`,
                                  }}
                                />
                                <strong>{number(next)}s</strong>
                              </div>
                            </div>
                          ))}
                        </div>
                        <div
                          className={`option-verdict ${active.comparison.feasible ? "pass" : "fail"}`}
                        >
                          {active.comparison.feasible ? (
                            <CheckCircle2 size={20} />
                          ) : (
                            <Info size={20} />
                          )}
                          <div>
                            <strong>
                              {active.comparison.feasible
                                ? "Within budget and cross-street limit"
                                : "Excluded from recommendation"}
                            </strong>
                            <p>
                              {active.comparison.rejection_reasons.join(". ") ||
                                `All planned trips completed. Cross-street change ${number(active.comparison.cross_delay_change_pct)}%.`}
                            </p>
                          </div>
                        </div>
                      </>
                    )}
                  </section>
                  <section className="panel frontier-panel">
                    <div className="panel-heading">
                      <h2>Cost versus delay</h2>
                      <Wallet size={18} />
                    </div>
                    <CostChart
                      alternatives={result.alternatives}
                      frontier={result.pareto_ids}
                    />
                    <div className="chart-legend">
                      <span>
                        <i className="dot green" />
                        Feasible
                      </span>
                      <span>
                        <i className="dot orange" />
                        Rejected
                      </span>
                    </div>
                    <p className="helper chart-help">
                      Larger dots mark nondominated cost/delay options. Capital
                      estimates use a log scale.
                    </p>
                    <div className="economic-estimate">
                      <span>Estimated net annual time value</span>
                      <strong>
                        {money(
                          recommendation.economics
                            .estimated_net_annual_value_cad,
                        )}
                      </strong>
                      <p>
                        Illustrative annualization of this period. Costs,
                        occupancy and time value are assumptions.
                      </p>
                    </div>
                  </section>
                </div>
                <section className="panel all-options">
                  <div className="panel-heading">
                    <h2>Decision ledger</h2>
                    {exportLink}
                  </div>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Option</th>
                          <th>Vehicle delay</th>
                          <th>Cross-street delay</th>
                          <th>Estimated capital</th>
                          <th>Outcome</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.alternatives.map((a) => (
                          <tr
                            key={a.id}
                            className={
                              a.id === recommendation.id ? "selected-row" : ""
                            }
                          >
                            <td>
                              <strong>{names[a.id]}</strong>
                              <small>{a.label}</small>
                            </td>
                            <td>{number(a.metrics.mean_delay_s)}s</td>
                            <td>{number(a.metrics.cross_mean_delay_s)}s</td>
                            <td>{money(a.capital_cost_cad)}</td>
                            <td>
                              <span
                                className={`badge ${a.comparison.feasible ? "green" : "amber"}`}
                              >
                                {a.id === recommendation.id
                                  ? "RECOMMENDED"
                                  : a.comparison.feasible
                                    ? "FEASIBLE"
                                    : "REJECTED"}
                              </span>
                              {a.comparison.rejection_reasons.map((reason) => (
                                <small key={reason}>{reason}</small>
                              ))}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="ledger-footer">
                    Evaluation seeds:{" "}
                    {result.evaluation.holdout_seeds.join(", ")} ·{" "}
                    {number(recommendation.metrics.completed)} completed/run ·{" "}
                    {number(recommendation.metrics.unserved)} unserved.
                    Selection uses these evaluation results; broader statistical
                    validation remains open.
                  </div>
                </section>
              </>
            ) : (
              <EmptyState onStudy={() => go(2)} />
            ))}
          {view === "evidence" && (
            <>
              <div className="evidence-grid">
                <section className="panel readiness">
                  <div className="panel-heading">
                    <h2>Data readiness</h2>
                    <span className="badge amber">CALIBRATION PENDING</span>
                  </div>
                  <div className="readiness-row">
                    <CheckCircle2 size={20} />
                    <div>
                      <strong>Calgary incident context</strong>
                      <p>
                        {incidents
                          ? `${incidents.raw_rows} rows · ${incidents.context_events} events after heuristic deduplication`
                          : "Loading snapshot"}
                      </p>
                      <a
                        href="https://data.calgary.ca/d/35ra-9556"
                        target="_blank"
                        rel="noreferrer"
                      >
                        City dataset <ArrowUpRight size={13} />
                      </a>
                    </div>
                    <span className="badge green">REAL DATA</span>
                  </div>
                  <div className="readiness-row pending">
                    <Info size={20} />
                    <div>
                      <strong>Directional traffic counts</strong>
                      <p>
                        {scenario.demand_kind === "measured"
                          ? scenario.demand_source
                          : "Default arrival rates are assumptions. Import a sourced flow profile."}
                      </p>
                      <label className="file-button">
                        Import flow JSON
                        <input
                          aria-label="Import flow JSON"
                          type="file"
                          disabled={busy}
                          accept=".json,application/json"
                          onChange={(e) => importProfile(e.target.files?.[0])}
                        />
                      </label>
                      {scenario.demand_kind === "measured" && (
                        <button
                          className="text-button"
                          disabled={busy}
                          onClick={() =>
                            setScenario({
                              ...defaults,
                              budget_cad: scenario.budget_cad,
                            })
                          }
                        >
                          Reset assumed arrivals
                        </button>
                      )}
                    </div>
                    <span
                      className={`badge ${scenario.demand_kind === "measured" ? "blue" : "amber"}`}
                    >
                      {scenario.demand_kind === "measured"
                        ? "IMPORTED"
                        : "ASSUMED"}
                    </span>
                  </div>
                  <div className="readiness-row pending">
                    <Info size={20} />
                    <div>
                      <strong>Geometry & observed signal timings</strong>
                      <p>
                        Synthetic three-junction network. OSM download exists
                        for investigation; it is not used here.
                      </p>
                    </div>
                    <span className="badge amber">SYNTHETIC</span>
                  </div>
                  <div className="readiness-row pending">
                    <Info size={20} />
                    <div>
                      <strong>Field validation & cost estimates</strong>
                      <p>
                        Observed queues, travel times and engineering estimates
                        needed before a City pilot.
                      </p>
                    </div>
                    <span className="badge neutral">OPEN</span>
                  </div>
                </section>
                <section className="panel method-panel">
                  <div className="panel-heading">
                    <h2>How the decision is made</h2>
                    <GitBranch size={18} />
                  </div>
                  <ol>
                    <li>
                      <strong>Inspect</strong>
                      <span>Read demand, budget and provenance.</span>
                    </li>
                    <li>
                      <strong>Propose & simulate</strong>
                      <span>Allocate green by demand. Run native SUMO.</span>
                    </li>
                    <li>
                      <strong>Evaluate & revise</strong>
                      <span>
                        Measure cross-street harm. Reduce change when guardrail
                        fails.
                      </span>
                    </li>
                    <li>
                      <strong>Compare & stress</strong>
                      <span>
                        Freeze options. Score paired arrivals, budget and ±20%
                        flow.
                      </span>
                    </li>
                  </ol>
                  <div className="method-note">
                    Deterministic tool-using policy agents. No trained RL model
                    or LLM calls. Engine failures are reported, never replaced
                    with invented numbers.
                  </div>
                </section>
              </div>
              <section className="panel trace-panel">
                <div className="panel-heading">
                  <h2>Decision trail</h2>
                  <span className="helper">
                    {job?.trace.length ?? 0} recorded actions
                    {job ? ` · ${job.status}` : ""}
                  </span>
                </div>
                {job?.trace.length ? (
                  <div className="trace-list">
                    {job.trace.map((entry, i) => (
                      <details key={`${entry.at_utc}-${i}`}>
                        <summary>
                          <span className="trace-number">
                            {String(i + 1).padStart(2, "0")}
                          </span>
                          <strong>{entry.agent}</strong>
                          <span className="trace-action">
                            {entry.action.replaceAll("_", " ")}
                          </span>
                          <time>
                            {new Date(entry.at_utc).toLocaleTimeString()}
                          </time>
                          <ChevronRight size={16} />
                        </summary>
                        <p>{entry.detail}</p>
                      </details>
                    ))}
                  </div>
                ) : (
                  <p className="empty-inline">
                    Run an experiment to inspect its actual reasoning and tool
                    trail.
                  </p>
                )}
              </section>
              <section className="panel incidents-panel">
                <div className="panel-heading">
                  <div>
                    <h2>Calgary incident snapshot</h2>
                    <p className="helper">
                      {incidents
                        ? `Retrieved ${new Date(incidents.source.retrieved_at_utc).toLocaleString("en-CA", { timeZone: "America/Edmonton" })} MDT`
                        : "Loading source"}
                    </p>
                  </div>
                  <a
                    className="text-link"
                    href="https://data.calgary.ca/d/35ra-9556"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open source <ArrowUpRight size={14} />
                  </a>
                </div>
                <p className="incident-caution">
                  Context only. These events may have cleared; incident records
                  do not measure traffic flow or establish congestion rankings.
                </p>
                <div className="incident-list">
                  {incidents?.records.slice(0, 4).map((incident, i) => (
                    <article key={i}>
                      <MapPin size={17} />
                      <div>
                        <strong>{incident.title}</strong>
                        <p>{incident.description}</p>
                      </div>
                      <span>
                        {new Date(incident.start_utc).toLocaleDateString(
                          "en-CA",
                          { timeZone: "America/Edmonton" },
                        )}
                      </span>
                    </article>
                  ))}
                </div>
              </section>
              {result && (
                <section className="panel assumptions-panel">
                  <div className="panel-heading">
                    <h2>Run assumptions & limitations</h2>
                    {exportLink}
                  </div>
                  <ul>
                    {result.limitations.map((l) => (
                      <li key={l}>{l}</li>
                    ))}
                  </ul>
                  <details>
                    <summary>Submitted inputs & simulator version</summary>
                    <p>{result.simulator_version}</p>
                    <pre>{JSON.stringify(result.scenario, null, 2)}</pre>
                  </details>
                </section>
              )}
            </>
          )}
          {view !== "evidence" && (
            <div className="wizard-footer">
              <button
                className="text-link"
                disabled={step === 1}
                onClick={() => go(step - 1)}
              >
                Back
              </button>
              <span>Step {step} of 4</span>
              {step === 1 ? (
                <button className="button primary" onClick={() => go(2)}>
                  Choose interventions <ChevronRight size={16} />
                </button>
              ) : step === 2 ? (
                <button
                  className="button primary"
                  disabled={busy}
                  onClick={start}
                >
                  Run simulation <Play size={15} />
                </button>
              ) : step === 3 ? (
                <button
                  className="button primary"
                  disabled={!result}
                  onClick={() => go(4)}
                >
                  Review recommendation <ChevronRight size={16} />
                </button>
              ) : (
                exportLink
              )}
            </div>
          )}
          <footer>
            <span>
              BOTTLENECK BUSTERS{" "}
              <span> / Planning evidence, before investment.</span>
            </span>
            <span>Local study · v0.1</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
