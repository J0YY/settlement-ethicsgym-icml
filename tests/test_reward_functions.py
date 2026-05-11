from segym.evaluators.deterministic import DeterministicEthicsEvaluator
from segym.rewards import defense_utility, ethics_penalty, plaintiff_utility
from segym.rewards import client_utility
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


def test_money_seeking_and_payer_roles_score_in_correct_direction():
    debt = load_scenario("data/scenarios/seed/debt_false_limitations_001.yaml")
    contract = load_scenario("data/scenarios/seed/contract_false_delivery_001.yaml")
    assert client_utility(debt, 5000, debt.agent_role) > client_utility(debt, 1000, debt.agent_role)
    assert client_utility(contract, 90000, contract.agent_role) > client_utility(contract, 190000, contract.agent_role)
