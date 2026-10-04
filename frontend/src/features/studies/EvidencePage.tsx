import { ArrowUpRight, CheckCircle2, ChevronRight, GitBranch, Info, MapPin } from "lucide-react";
import { defaults } from "./model";
import type { StudyPageProps } from "./page-types";
import { ReportLink } from "./ReportLink";
export function EvidencePage({ controller, step, go, onEvidence }: StudyPageProps) {
  const { scenario, setScenario, incidents, job, result, busy, change, importProfile } = controller;
  const exportLink = <ReportLink controller={controller} />;
  return (<>
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
            <a href="https://data.calgary.ca/d/35ra-9556" target="_blank" rel="noreferrer">
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
              <input aria-label="Import flow JSON" type="file" disabled={busy} accept=".json,application/json" onChange={(e) => importProfile(e.target.files?.[0])} />
            </label>
            {scenario.demand_kind === "measured" && (<button className="text-button" disabled={busy} onClick={() => setScenario({
              ...defaults,
              budget_cad: scenario.budget_cad,
            })}>
              Reset assumed arrivals
            </button>)}
          </div>
          <span className={`badge ${scenario.demand_kind === "measured" ? "blue" : "amber"}`}>
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
      {job?.trace.length ? (<div className="trace-list">
        {job.trace.map((entry, i) => (<details key={`${entry.at_utc}-${i}`}>
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
        </details>))}
      </div>) : (<p className="empty-inline">
        Run an experiment to inspect its actual reasoning and tool
        trail.
      </p>)}
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
        <a className="text-link" href="https://data.calgary.ca/d/35ra-9556" target="_blank" rel="noreferrer">
          Open source <ArrowUpRight size={14} />
        </a>
      </div>
      <p className="incident-caution">
        Context only. These events may have cleared; incident records
        do not measure traffic flow or establish congestion rankings.
      </p>
      <div className="incident-list">
        {incidents?.records.slice(0, 4).map((incident, i) => (<article key={i}>
          <MapPin size={17} />
          <div>
            <strong>{incident.title}</strong>
            <p>{incident.description}</p>
          </div>
          <span>
            {new Date(incident.start_utc).toLocaleDateString("en-CA", { timeZone: "America/Edmonton" })}
          </span>
        </article>))}
      </div>
    </section>
    {result && (<section className="panel assumptions-panel">
      <div className="panel-heading">
        <h2>Run assumptions & limitations</h2>
        {exportLink}
      </div>
      <ul>
        {result.limitations.map((l) => (<li key={l}>{l}</li>))}
      </ul>
      <details>
        <summary>Submitted inputs & simulator version</summary>
        <p>{result.simulator_version}</p>
        <pre>{JSON.stringify(result.scenario, null, 2)}</pre>
      </details>
    </section>)}
  </>);
}
