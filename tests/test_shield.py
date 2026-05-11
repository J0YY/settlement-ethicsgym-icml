from segym.agents import ScriptedDeceptiveAgent, ShieldedAgent
from segym.agents.factory import build_agent
from segym.evaluators.deterministic import DeterministicEthicsEvaluator
from segym.env import SettlementEthicsEnv
from segym.scenario import load_scenario


def test_shield_blocks_false_policy_limit_by_rewrite():
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/pi_policy_limits_001.yaml")
    obs = env.reset(seed=1)
    action = ShieldedAgent(ScriptedDeceptiveAgent(), mode="rewrite").act(obs)
    assert "only available coverage" not in action.public_message.lower()


def test_shield_allows_value_estimate():
    scenario = load_scenario("data/scenarios/seed/pi_policy_limits_001.yaml")
    findings = DeterministicEthicsEvaluator().evaluate("We think your demand is far above the settlement value.", scenario)
    assert not any(f.severity >= 3 for f in findings)


def test_rewrite_removes_only_false_claim_not_offer():
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/pi_policy_limits_001.yaml")
    obs = env.reset(seed=1)
    action = ShieldedAgent(ScriptedDeceptiveAgent(), mode="rewrite").act(obs)
    assert action.offer.amount_usd == 70000
    assert "$70,000" in action.public_message


def test_factory_passes_shield_mode_and_base_type():
    agent = build_agent("shielded_deceptive", shield_mode="block", base_type="scripted_honest")
    assert agent.mode == "block"
    assert agent.base_agent.model_id == "scripted_honest"
