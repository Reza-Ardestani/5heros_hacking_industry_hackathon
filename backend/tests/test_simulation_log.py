import json

from app.application.jobs import JobManager
from app.application.planner import PlanningService
from app.domain.evaluation import explain_decision
from app.domain.models import Scenario
from app.infra.disruption_store import Store
from app.infra.simulation import SumoSimulator
from app.infra.simulation_log import SimulationRecorder


def _row(id_, delay, cross=10.0, cost=0.0, feasible=True, details=()):
    return {
        "id": id_, "label": id_, "capital_cost_cad": cost,
        "metrics": {"total_delay_s": delay, "mean_delay_s": delay / 100, "cross_mean_delay_s": cross},
        "comparison": {"feasible": feasible, "rejection_details": list(details)},
    }  # fmt: skip


def test_decision_names_lowest_delay_option_and_the_setting_that_blocks_it():
    guard = {"rule": "cross_street", "setting": "cross_guardrail_pct", "observed": 88.96,
             "limit": 30, "message": "Cross-street delay +89% exceeds the 30% limit"}  # fmt: skip
    budget = {"rule": "budget", "setting": "budget_cad", "observed": 1_200_000, "limit": 100_000,
              "message": "Capital $1,200,000 exceeds the $100,000 budget"}  # fmt: skip
    rows = [
        _row("reference", 10000),
        _row("candidate", 5400, feasible=False, details=[guard]),
        _row("revised", 7200, cost=15000),
        _row("capacity", 8000, cost=1_200_000, feasible=False, details=[budget]),
    ]
    d = explain_decision(rows, "revised")
    assert d["lowest_delay_id"] == "candidate" and not d["lowest_delay_is_recommended"]
    assert d["lowest_delay_rejected_because"] == [guard["message"]]
    change = d["what_would_change"][0]
    assert change["id"] == "candidate" and change["settings"][0]["needed"] == 90
    assert [c["id"] for c in d["what_would_change"]] == ["candidate"]  # capacity is slower


def test_real_study_is_logged_to_database_and_jsonl(tmp_path):
    store = Store(tmp_path / "db.sqlite")
    recorder = SimulationRecorder(lambda: store, runs_dir=tmp_path / "runs")
    jobs = JobManager(PlanningService(SumoSimulator()), recorder)
    run_id = jobs.submit(Scenario(duration_s=300), {"origin": "test"})
    jobs.pool.shutdown(wait=True)
    job = jobs.get(run_id)
    assert job["status"] == "completed", job["error"]
    result = job["result"]
    assert result["decision"]["recommended_id"] == result["recommended_id"]
    stress = result["cost_stress"]
    assert stress["recommended_id"] == result["recommended_id"] and len(stress["grid"]) == 5
    assert stress["grid"][2][2] == result["recommended_id"]  # unchanged costs and budget

    run = store.get_sim(run_id)
    assert run["status"] == "completed" and run["origin"] == "test"
    assert len(run["actions"]) == len(job["trace"]) and run["actions"][0]["seq"] == 1
    assert {a["alt_id"] for a in run["alternatives"]} == {
        "reference",
        "candidate",
        "revised",
        "capacity",
    }
    # 4 tuning + 12 hold-out + 4 stress trials, each with metrics and hashes.
    purposes = [t["purpose"] for t in run["trials"]]
    assert purposes.count("tuning") == 4 and purposes.count("holdout") == 12
    assert purposes.count("stress") == 4
    assert all(t["demand_sha256"] and t["metrics"]["planned"] for t in run["trials"])
    lines = (tmp_path / "runs" / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()
    kinds = [json.loads(line)["type"] for line in lines]
    assert (
        kinds[0] == "start" and kinds[-1] == "result" and kinds.count("action") == len(job["trace"])
    )
