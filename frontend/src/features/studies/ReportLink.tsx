import { Download } from "lucide-react";
import { reportUrl } from "./api";
import type { StudyController } from "./useStudy";
export function ReportLink({ controller }: {
  controller: StudyController;
}) {
  const { result, busy, job } = controller;
  return (<a className={`button secondary ${!result || busy ? "disabled" : ""}`} aria-disabled={!result || busy} href={result && !busy ? reportUrl(job!.id) : "#"} download onClick={(e) => {
    if (!result || busy)
      e.preventDefault();
  }}>
    <Download size={16} />
    Export report
  </a>);
}
