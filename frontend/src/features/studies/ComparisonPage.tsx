import { CheckCircle2, Info, Wallet } from "lucide-react";
import { CostStressPanel } from "./CostStressPanel";
import { kindNote, money, number, optionName } from "./format";
import type { StudyPageProps } from "./page-types";
import { ReportLink } from "./ReportLink";
import { CostChart, Decision, EmptyState, JobStatus } from "./StudyComponents";
import { EvidenceSummaryPanel } from "./StudyDesign";
export function ComparisonPage({ controller, step, go, onEvidence }: StudyPageProps) {
  const { job, submitting, pollError, selected, setSelected, result, reference, recommendation, active, busy, change } = controller;
  const exportLink = <ReportLink controller={controller} />;
  return (busy || job?.status === "failed" ? (<JobStatus job={job ?? null} submitting={submitting} pollError={pollError} onStudy={() => go(2)} />) : result && recommendation && reference ? (<>
    <Decision result={result} recommendation={recommendation} reference={reference} />
    <div className="comparison-cards">
      {result.alternatives.map((a) => (<button key={a.id} className={`option-card ${a.id === selected ? "focused" : ""} ${a.id === recommendation.id ? "recommended" : ""}`} onClick={() => setSelected(a.id)}>
        <div>
          <span className="option-title">
            {optionName(a.id, a.label)}
          </span>
          <span className="option-badges">
            <span className={`badge ${a.id === recommendation.id ? "green" : a.comparison.feasible ? "neutral" : "amber"}`}>
              {a.id === recommendation.id
                ? "RECOMMENDED"
                : a.comparison.feasible
                  ? "FEASIBLE"
                  : "REJECTED"}
            </span>
            {result.decision?.lowest_delay_id === a.id && (<span className="badge blue">LOWEST DELAY</span>)}
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
        {!a.comparison.feasible && (<span className="option-reason">
          {(a.comparison.rejection_details ?? [])
            .map((d) => d.message)
            .join(" · ") || a.comparison.rejection_reasons.join(" · ")}
        </span>)}
      </button>))}
    </div>
    <EvidenceSummaryPanel result={result} />
    <CostStressPanel result={result} />
    <div className="compare-layout">
      <section className="panel comparison-detail">
        <div className="panel-heading">
          <h2>
            {optionName(active?.id ?? "reference", active?.label)} versus
            reference plan
          </h2>
          <span className="helper">3 paired seeds · means</span>
        </div>
        {active && (<>
          <div className="comparison-bars">
            {([
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
            ] as [
              string,
              number,
              number
            ][]).map(([label, base, next]) => (<div className="bar-pair" key={label}>
              <h3>{label}</h3>
              <div>
                <span>Reference</span>
                <i style={{
                  width: `${(base / Math.max(base, next, 1)) * 62}%`,
                }} />
                <strong>{number(base)}s</strong>
              </div>
              <div>
                <span>Option</span>
                <i className="option-bar" style={{
                  width: `${(next / Math.max(base, next, 1)) * 62}%`,
                }} />
                <strong>{number(next)}s</strong>
              </div>
            </div>))}
          </div>
          <div className={`option-verdict ${active.comparison.feasible ? "pass" : "fail"}`}>
            {active.comparison.feasible ? (<CheckCircle2 size={20} />) : (<Info size={20} />)}
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
        </>)}
      </section>
      <section className="panel frontier-panel">
        <div className="panel-heading">
          <h2>Cost versus delay</h2>
          <Wallet size={18} />
        </div>
        <CostChart alternatives={result.alternatives} frontier={result.pareto_ids} />
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
            {money(recommendation.economics
              .estimated_net_annual_value_cad)}
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
            {result.alternatives.map((a) => (<tr key={a.id} className={a.id === recommendation.id ? "selected-row" : ""}>
              <td>
                <strong>{optionName(a.id, a.label)}</strong>
                <small>{a.label}</small>
              </td>
              <td>{number(a.metrics.mean_delay_s)}s</td>
              <td>{number(a.metrics.cross_mean_delay_s)}s</td>
              <td>{money(a.capital_cost_cad)}</td>
              <td>
                <span className={`badge ${a.comparison.feasible ? "green" : "amber"}`}>
                  {a.id === recommendation.id
                    ? "RECOMMENDED"
                    : a.comparison.feasible
                      ? "FEASIBLE"
                      : "REJECTED"}
                </span>
                {a.comparison.rejection_reasons.map((reason) => (<small key={reason}>{reason}</small>))}
              </td>
            </tr>))}
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
  </>) : (<EmptyState onStudy={() => go(2)} />));
}
