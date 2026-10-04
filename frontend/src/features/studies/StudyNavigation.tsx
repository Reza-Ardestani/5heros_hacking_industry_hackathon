import { ChevronRight, Play } from "lucide-react";
import type { StudyPageProps } from "./page-types";
import { ReportLink } from "./ReportLink";
export function StudyNavigation({ controller, step, go, onEvidence }: StudyPageProps) {
  const { result, recommendation, busy, start } = controller;
  const exportLink = <ReportLink controller={controller} />;
  return (<div className="wizard-footer">
    <button className="text-link" disabled={step === 1} onClick={() => go(step - 1)}>
      Back
    </button>
    <span>Step {step} of 4</span>
    {step === 1 ? (<button className="button primary" onClick={() => go(2)}>
      Choose interventions <ChevronRight size={16} />
    </button>) : step === 2 ? (<button className="button primary" disabled={busy} onClick={start}>
      Run simulation <Play size={15} />
    </button>) : step === 3 ? (<button className="button primary" disabled={!result} onClick={() => go(4)}>
      Review recommendation <ChevronRight size={16} />
    </button>) : (exportLink)}
  </div>);
}
