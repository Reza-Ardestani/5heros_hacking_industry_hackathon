"""Study = planner run + six-month evidence summary (when an intersection is attached)."""

from datetime import UTC, datetime

from app.application.study_summary import build_summary


class StudyService:
    def __init__(self, planner):
        self.planner = planner

    def run(self, scenario, emit, context=None):
        result = self.planner.run(scenario, emit, context)
        result["evidence_summary"] = build_summary(result, context)
        emit(
            {
                "at_utc": datetime.now(UTC).isoformat(),
                "agent": "Reporting agent",
                "action": "evidence_summary",
                "detail": result["evidence_summary"]["headline"],
                "options_that_reduce_delay": result["evidence_summary"][
                    "options_that_reduce_delay"
                ],
            }
        )
        return result
