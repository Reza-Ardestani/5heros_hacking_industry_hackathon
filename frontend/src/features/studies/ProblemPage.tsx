import { ArrowUpRight, Clock3, MapPin, ShieldCheck, Wallet } from "lucide-react";
import type { StudyPageProps } from "./page-types";
import { ReportLink } from "./ReportLink";
export function ProblemPage({ controller, step, go, onEvidence }: StudyPageProps) {
  const { scenario, study, change } = controller;
  const exportLink = <ReportLink controller={controller} />;
  return (<>
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
          {Array.from({ length: 12 }, (_, i) => (<span key={i} style={{
            left: `${16 + i * 5.5}%`,
            top: i % 2 === 0 ? "44%" : "56%",
          }} />))}
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
      <button className="text-link" onClick={() => onEvidence()}>
        Inspect data readiness <ArrowUpRight size={15} />
      </button>
    </section>
  </>);
}
