"""Record every simulation study: database rows plus a JSON-lines log file per run.

Database tables (see infra/disruption_store.py): sim_runs, sim_actions, sim_alternatives,
sim_trials. Log files: data/runs/<run_id>.jsonl (git-ignored), one line per agent action
followed by a final "result" line. Recording failures are logged and never fail a study.
"""

import json
import logging
from pathlib import Path

from app.infra.disruption_store import ROOT

RUNS_DIR = ROOT / "data" / "runs"
log = logging.getLogger(__name__)


class SimulationRecorder:
    def __init__(self, store_getter, runs_dir=RUNS_DIR):
        self.store_getter, self.runs_dir = store_getter, Path(runs_dir)
        self.seq = {}

    def _safe(self, fn, *args):
        try:
            fn(*args)
        except Exception:
            log.exception("Simulation recording failed")

    def _append(self, run_id, record):
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        with (self.runs_dir / f"{run_id}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

    def start(self, run_id, scenario, meta=None):
        meta = meta or {}
        self.seq[run_id] = 0
        path = str(self.runs_dir / f"{run_id}.jsonl")
        self._safe(
            self.store_getter().start_sim, run_id, scenario, meta.get("origin", "manual"),
            meta.get("intersection_key"), path,
        )  # fmt: skip
        self._safe(self._append, run_id, {"type": "start", "scenario": scenario, **meta})

    def event(self, run_id, event):
        self.seq[run_id] = self.seq.get(run_id, 0) + 1
        self._safe(self.store_getter().add_sim_action, run_id, self.seq[run_id], event)
        self._safe(self._append, run_id, {"type": "action", "seq": self.seq[run_id], **event})

    def finish(self, run_id, result):
        self._safe(self.store_getter().finish_sim, run_id, result, result.get("evidence_summary"))
        compact = {
            "type": "result",
            "recommended_id": result.get("recommended_id"),
            "decision": result.get("decision"),
            "alternatives": [
                {"id": a["id"], "label": a["label"], "metrics": a["metrics"],
                 "comparison": a["comparison"]}
                for a in result.get("alternatives", [])
            ],
        }  # fmt: skip
        self._safe(self._append, run_id, compact)
        self.seq.pop(run_id, None)

    def fail(self, run_id, error):
        self._safe(self.store_getter().fail_sim, run_id, error)
        self._safe(self._append, run_id, {"type": "failed", "error": error})
        self.seq.pop(run_id, None)
