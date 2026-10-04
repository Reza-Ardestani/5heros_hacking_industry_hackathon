import type { View } from "../../shared/navigation";
import { ComparisonPage } from "./ComparisonPage";
import { EvidencePage } from "./EvidencePage";
import type { StudyPageProps } from "./page-types";
import { ProblemPage } from "./ProblemPage";
import { StudyNavigation } from "./StudyNavigation";
import { StudyPage } from "./StudyPage";
export function StudiesWorkspace({ view, ...props }: StudyPageProps & {
  view: View;
}) {
  return <>
    {view === "problem" && <ProblemPage {...props} />}
    {view === "study" && <StudyPage {...props} />}
    {view === "compare" && <ComparisonPage {...props} />}
    {view === "evidence" && <EvidencePage {...props} />}
    {view !== "evidence" && <StudyNavigation {...props} />}
  </>;
}
