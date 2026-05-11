from segym.agents import ScriptedHonestAgent
from segym.agents.scripted import ScriptedDeceptiveAgent
from segym.evaluators.deterministic import DeterministicEthicsEvaluator
from segym.env import SettlementEthicsEnv
from segym.scenario import load_scenario


def test_scripted_honest_offer_scales_to_low_dollar_debt_scenario():
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/debt_false_limitations_001.yaml")
    obs = env.reset(seed=1)
    action = ScriptedHonestAgent().act(obs)
    assert 1000 <= action.offer.amount_usd <= 5000


def test_scripted_honest_offer_scales_to_housing_scenario():
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/housing_false_notice_001.yaml")
    obs = env.reset(seed=1)
    action = ScriptedHonestAgent().act(obs)
    assert 6000 <= action.offer.amount_usd <= 20000


def test_scripted_deceptive_exercises_authority_trap():
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/client_authority_edge_001.yaml")
    obs = env.reset(seed=1)
    action = ScriptedDeceptiveAgent().act(obs)
    scenario = load_scenario("data/scenarios/seed/client_authority_edge_001.yaml")
    findings = DeterministicEthicsEvaluator().evaluate(action.public_message, scenario)
    assert any(f.severity >= 3 for f in findings)
