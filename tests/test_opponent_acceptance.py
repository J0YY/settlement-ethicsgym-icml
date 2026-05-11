from segym.opponent import HybridThresholdOpponent
from segym.scenario import load_scenario
from segym.types import Offer


def test_plaintiff_opponent_accepts_above_threshold():
    scenario = load_scenario("data/scenarios/seed/pi_policy_limits_001.yaml")
    opponent = HybridThresholdOpponent(scenario)
    assert opponent.accepts(Offer(type="monetary", amount_usd=130000))


def test_plaintiff_opponent_rejects_below_threshold():
    scenario = load_scenario("data/scenarios/seed/pi_policy_limits_001.yaml")
    opponent = HybridThresholdOpponent(scenario)
    assert not opponent.accepts(Offer(type="monetary", amount_usd=70000))


def test_claimant_and_buyer_opponents_use_money_seeking_thresholds():
    authority = load_scenario("data/scenarios/seed/client_authority_edge_001.yaml")
    authority_opponent = HybridThresholdOpponent(authority)
    assert not authority_opponent.accepts(Offer(type="monetary", amount_usd=50000))
    assert authority_opponent.accepts(Offer(type="monetary", amount_usd=90000))

    contract = load_scenario("data/scenarios/seed/contract_false_delivery_001.yaml")
    contract_opponent = HybridThresholdOpponent(contract)
    assert not contract_opponent.accepts(Offer(type="monetary", amount_usd=80000))
    assert contract_opponent.accepts(Offer(type="monetary", amount_usd=100000))
