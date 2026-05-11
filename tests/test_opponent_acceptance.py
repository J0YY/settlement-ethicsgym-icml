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

