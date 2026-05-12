from segym.agents.best_of_n import BestOfNEthicsAwareAgent, BestOfNUtilityAgent, estimated_utility
from segym.env import SettlementEthicsEnv
from segym.types import AgentAction, Offer


def test_best_of_n_utility_uses_collector_as_money_seeking_role():
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/debt_false_limitations_001.yaml")
    obs = env.reset(seed=1)
    low = AgentAction(public_message="Offer low", offer=Offer(type="monetary", amount_usd=1000))
    high = AgentAction(public_message="Offer high", offer=Offer(type="monetary", amount_usd=5000))
    assert estimated_utility(high, obs) > estimated_utility(low, obs)


def test_best_of_n_utility_uses_seller_as_payer_role():
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/contract_false_delivery_001.yaml")
    obs = env.reset(seed=1)
    low = AgentAction(public_message="Offer low", offer=Offer(type="monetary", amount_usd=90000))
    high = AgentAction(public_message="Offer high", offer=Offer(type="monetary", amount_usd=190000))
    assert estimated_utility(low, obs) > estimated_utility(high, obs)


def test_best_of_n_utility_records_unsafe_selection_when_safe_candidate_exists():
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/pi_policy_limits_001.yaml")
    obs = env.reset(seed=1)
    action = BestOfNUtilityAgent(n=4).act(obs)

    metadata = action.metadata["best_of_n"]
    assert metadata["safe_candidate_available"] is True
    assert metadata["selected_unsafe_despite_safe"] is True


def test_best_of_n_ethics_records_safe_selection():
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/pi_policy_limits_001.yaml")
    obs = env.reset(seed=1)
    action = BestOfNEthicsAwareAgent(n=4).act(obs)

    metadata = action.metadata["best_of_n"]
    assert metadata["safe_candidate_available"] is True
    assert metadata["selected_unsafe_despite_safe"] is False
