import { Check } from "lucide-react";
import type { View } from "../../shared/navigation";
import type { StudyController } from "./useStudy";
export function StudyProgress({ view, step, go, controller }: {
  view: View;
  step: number;
  go: (step: number) => void;
  controller: StudyController;
}) {
  const { job, result } = controller;
  return <>{view !== "evidence" && view !== "intersections" && (<div className="wizard-progress" aria-label="Study progress">
    {[
      "Frame the problem",
      "Choose interventions",
      "Run simulation",
      "Review recommendation",
    ].map((label, i) => (<button key={label} className={step === i + 1 ? "current" : step > i + 1 ? "done" : ""} aria-current={step === i + 1 ? "step" : undefined} disabled={(i === 2 && !job) || (i === 3 && !result)} onClick={() => go(i + 1)}>
      <span>{step > i + 1 ? <Check size={13} /> : i + 1}</span>
      <strong>{label}</strong>
    </button>))}
  </div>)}</>;
}
