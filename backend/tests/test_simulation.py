from app.domain.models import Intervention, Scenario
from app.infra.simulation import SumoSimulator


def test_real_sumo_all_demand_accounted_and_paired_manifest():
    simulator = SumoSimulator()
    scenario = Scenario(duration_s=300)
    reference = simulator.run(scenario, Intervention("reference", "Reference", 0.5, 1, 0), 42)
    candidate = simulator.run(scenario, Intervention("candidate", "Candidate", 0.58, 1, 15000), 42)
    assert reference["demand_sha256"] == candidate["demand_sha256"]
    assert reference["network_sha256"] != candidate["network_sha256"]
    for trial in (reference, candidate):
        metrics = trial["metrics"]
        assert (
            metrics["planned"]
            == metrics["completed"] + metrics["unfinished"] + metrics["uninserted"]
        )
        assert metrics["unserved"] == 0
        assert trial["teleports"] == 0
        assert metrics["total_delay_s"] >= metrics["departure_delay_s"] >= 0
        assert metrics["total_delay_s"] > 0 and metrics["max_queue"] > 0
    assert candidate["metrics"]["main_mean_delay_s"] < reference["metrics"]["main_mean_delay_s"]
