from segym.agents.best_of_n import estimated_utility
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
