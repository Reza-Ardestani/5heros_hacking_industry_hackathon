import type { StudyController } from "./useStudy";
export type StudyPageProps = {
  controller: StudyController;
  step: number;
  go: (step: number) => void;
  onEvidence: () => void;
};
