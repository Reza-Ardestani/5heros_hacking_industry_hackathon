import { ArrowUpRight, Check, ChevronRight, Clock3, Info, Loader2, MapPin, Pause, Play, RotateCcw, Settings2, ShieldCheck, Wallet } from "lucide-react";
import { SettingsAdvisor, SimulationLog } from "./DecisionExplain";
import { money, number, optionName } from "./format";
import { defaults } from "./model";
import type { StudyPageProps } from "./page-types";
import { ReportLink } from "./ReportLink";
import { Decision, JobStatus, Network, Stat } from "./StudyComponents";
import { EvidenceSummaryPanel, StudyBanner, StudyDesign, TestPlan } from "./StudyDesign";
import type { Scenario } from "./types";
export function StudyPage({ controller, step, go, onEvidence }: StudyPageProps) {
  const { scenario, setScenario, incidents, study, setStudy, job, submitting, pollError, selected, setSelected, frame, setFrame, playing, setPlaying, advanced, setAdvanced, result, reference, recommendation, active, busy, frames, current, averageFlow, change, start } = controller;
  const exportLink = <ReportLink controller={controller} />;
  return (<>
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
      <button onClick={() => onEvidence()}>
        Check data readiness <ArrowUpRight size={14} />
      </button>
    </div>
    {study && (<StudyBanner study={study} onClear={() => {
      setStudy(null);
      setScenario(defaults);
    }} />)}
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
          <input id="budget" aria-label="Capital budget" type="number" min="0" max="10000000" step="5000" disabled={busy} value={scenario.budget_cad} onChange={(e) => change("budget_cad", +e.target.value)} />
        </div>
        <div className="flow-field">
          <label htmlFor="main-flow">
            Arterial arrivals{" "}
            <strong>{number(averageFlow("main_vph"))}</strong>
          </label>
          <div className="unit">vehicles / hour / direction</div>
          <input id="main-flow" type="range" min="50" max="1800" step="25" disabled={busy || scenario.demand_kind === "measured"} value={averageFlow("main_vph")} onChange={(e) => change("main_vph", +e.target.value)} />
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
          <input id="cross-flow" type="range" min="20" max="600" step="10" disabled={busy || scenario.demand_kind === "measured"} value={averageFlow("cross_vph")} onChange={(e) => change("cross_vph", +e.target.value)} />
          <div className="range-ends">
            <span>20</span>
            <span>600</span>
          </div>
        </div>
        <label className="field-label" htmlFor="guardrail">
          Protect cross-street travel
        </label>
        <div className="number-input">
          <input id="guardrail" aria-label="Cross-street delay guardrail" type="number" min="0" max="200" disabled={busy} value={scenario.cross_guardrail_pct} onChange={(e) => change("cross_guardrail_pct", +e.target.value)} />
          <span>% max. delay increase</span>
        </div>
        <p className="helper guardrail-help">
          Plans exceeding this limit are rejected.
        </p>
        <StudyDesign scenario={scenario} disabled={busy} onChange={(patch) => setScenario((s) => ({ ...s, ...patch }))} />
        <button className="disclosure" aria-expanded={advanced} onClick={() => setAdvanced(!advanced)}>
          Costs & assumptions{" "}
          <ChevronRight size={16} className={advanced ? "rotated" : ""} />
        </button>
        {advanced && (<div className="advanced-grid">
          {([
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
          ] as [
            keyof Scenario,
            string
          ][]).map(([key, label]) => (<label key={key}>
            {label}
            <input aria-label={label} type="number" disabled={busy} value={scenario[key] as number} onChange={(e) => change(key, +e.target.value)} />
          </label>))}
        </div>)}
        <button className="button primary run-button" onClick={start} disabled={busy}>
          {busy ? (<>
            <Loader2 size={18} className="spinner" />
            Running simulation…
          </>) : (<>
            <Play size={17} fill="currentColor" />
            {result ? "Run updated study" : "Run simulation"}
          </>)}
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
        {step === 2 && (<SettingsAdvisor scenario={scenario} result={result} onApply={change} disabled={busy} />)}
        {step === 2 && <TestPlan scenario={scenario} />}
        {step === 3 && (<section className="panel network-panel">
          <div className="panel-heading">
            <div>
              <h2>Corridor simulation</h2>
              <p className="helper">
                {active
                  ? optionName(active.id, active.label)
                  : "Your experiment starts here"}
              </p>
            </div>
            <span className={`badge ${busy ? "blue" : "neutral"}`}>
              {busy
                ? "RUNNING"
                : result
                  ? "COMPLETED"
                  : job?.status === "failed"
                    ? "FAILED"
                    : "READY TO RUN"}
            </span>
          </div>
          <div className="scenario-tabs" aria-label="Playback alternative">
            {(result?.alternatives.map((a) => a.id) ?? [
              "reference",
              "candidate",
              "revised",
              "capacity",
            ]).map((id) => (<button key={id} disabled={!result} className={selected === id ? "active" : ""} onClick={() => {
              setSelected(id);
              setFrame(30);
              setPlaying(false);
            }}>
              {optionName(id, result?.alternatives.find((a) => a.id === id)?.label)}
              {result?.recommended_id === id && (<Check size={14} />)}
            </button>))}
          </div>
          <Network current={current} active={active} />
          <div className="playback-controls">
            <button aria-label={playing ? "Pause playback" : "Play playback"} disabled={!frames.length} onClick={() => setPlaying(!playing)}>
              {playing ? <Pause size={17} /> : <Play size={17} />}
            </button>
            <button aria-label="Restart playback" disabled={!frames.length} onClick={() => setFrame(0)}>
              <RotateCcw size={16} />
            </button>
            <input aria-label="Simulation playback time" type="range" min="0" max={Math.max(1, frames.length - 1)} value={Math.min(frame, Math.max(0, frames.length - 1))} disabled={!frames.length} onChange={(e) => {
              setPlaying(false);
              setFrame(+e.target.value);
            }} />
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
        </section>)}
        {busy || job?.status === "failed" ? (<JobStatus job={job ?? null} submitting={submitting} pollError={pollError} onStudy={() => go(2)} />) : recommendation && reference ? (<>
          <Decision result={result!} recommendation={recommendation} reference={reference} onCompare={() => go(4)} />
          <div className="study-stats">
            <Stat icon={<Clock3 size={17} />} label="Average vehicle delay" value={`${number(recommendation.metrics.mean_delay_s)}s`} note={`${number(reference.metrics.mean_delay_s)}s in reference plan`} />
            <Stat icon={<Wallet size={17} />} label="Estimated capital" value={money(recommendation.capital_cost_cad)} note={`Budget ${money(result!.scenario.budget_cad)}`} />
            <Stat icon={<ShieldCheck size={17} />} label="Cross-street change" value={`${number(recommendation.comparison.cross_delay_change_pct)}%`} note={`Limit ${result!.scenario.cross_guardrail_pct}% increase`} />
          </div>
          {step === 3 && result && <EvidenceSummaryPanel result={result} />}
          {step === 3 && job && <SimulationLog job={job} />}
        </>) : (<section className="panel start-guide">
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
        </section>)}
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
      <button onClick={() => onEvidence()}>
        View sources <ArrowUpRight size={15} />
      </button>
    </section>
  </>);
}
