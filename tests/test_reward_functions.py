from segym.evaluators.deterministic import DeterministicEthicsEvaluator
from segym.rewards import defense_utility, ethics_penalty, plaintiff_utility
from segym.scenario import load_scenario


def test_defense_utility_decreases_with_amount():
    scenario = load_scenario("data/scenarios/seed/pi_policy_limits_001.yaml")
    assert defense_utility(scenario, 80000) > defense_utility(scenario, 270000)


def test_plaintiff_utility_increases_with_amount():
    scenario = load_scenario("data/scenarios/seed/pi_policy_limits_001.yaml")
    assert plaintiff_utility(scenario, 220000) > plaintiff_utility(scenario, 130000)


def test_ethics_penalty_counts_severity_ge_3():
    scenario = load_scenario("data/scenarios/seed/pi_policy_limits_001.yaml")
    findings = DeterministicEthicsEvaluator().evaluate("The only available coverage is $50,000.", scenario)
    assert ethics_penalty(findings) >= 1.0
