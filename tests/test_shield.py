from segym.agents import LLMVerifiedShieldedAgent, ScriptedDeceptiveAgent, ShieldedAgent
from segym.agents.factory import build_agent
from segym.evaluators.deterministic import DeterministicEthicsEvaluator
from segym.evaluators.llm_judge import LLMJudge
from segym.env import SettlementEthicsEnv
from segym.scenario import load_scenario
from segym.types import EthicsFinding


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


def test_factory_builds_shielded_llm_base(monkeypatch):
    monkeypatch.setenv("SEGYN_FAKE_MODEL", "1")
    agent = build_agent(
        "shielded",
        model_id="shielded_llm",
        base_type="llm",
        base_model_id="utility_llm_base",
        model_name="fake-model",
        system_prompt_path="segym/prompts/agent_utility_system.txt",
        shield_mode="rewrite",
    )
    assert agent.model_id == "shielded_llm"
    assert agent.base_agent.model_id == "utility_llm_base"

    env = SettlementEthicsEnv.from_path("data/scenarios/seed/pi_policy_limits_001.yaml")
    action = agent.act(env.reset(seed=1))

    assert action.metadata["llm"]["provider"] == "fake"
    assert action.metadata["shield"]["triggered"] is False


def test_shield_records_rewrite_metadata():
    env = SettlementEthicsEnv.from_path(
        "data/scenarios/seed/pi_policy_limits_001.yaml",
        config={"model_id": "shielded_deceptive"},
    )
    obs = env.reset(seed=1)
    action = ShieldedAgent(ScriptedDeceptiveAgent(), mode="rewrite").act(obs)
    env.step(action)

    assert action.metadata["shield"]["triggered"] is True
    assert action.metadata["shield"]["action"] == "rewrite"
    assert "FALSE_MATERIAL_FACT" in action.metadata["shield"]["risky_labels"]
    assert env.result().metadata["shield_triggered"] is True
    assert env.result().metadata["shield_trigger_count"] == 1


def test_llm_verified_shield_rewrites_when_verifier_flags(monkeypatch):
    def fake_evaluate(self, message, scenario):
        return [
            EthicsFinding(
                text="unsafe paraphrase",
                label="MISLEADING_HALF_TRUTH",
                severity=3,
                confidence="high",
                short_rationale="Verifier found a misleading half-truth.",
                evaluator_name="llm_verifier_shield",
            )
        ]

    monkeypatch.setattr(LLMJudge, "evaluate", fake_evaluate)
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/pi_policy_limits_001.yaml")
    obs = env.reset(seed=1)

    action = LLMVerifiedShieldedAgent(ScriptedDeceptiveAgent(), verifier_fake=True).act(obs)

    assert "only available coverage" not in action.public_message.lower()
    assert action.metadata["shield"]["triggered"] is True
    assert action.metadata["shield"]["verifier"] == "llm_judge"
    assert "MISLEADING_HALF_TRUTH" in action.metadata["shield"]["risky_labels"]


def test_factory_builds_llm_verified_shielded_base(monkeypatch):
    monkeypatch.setenv("SEGYN_FAKE_MODEL", "1")

    agent = build_agent(
        "llm_verified_shielded",
        model_id="verified",
        base_type="llm",
        base_model_id="verified_base",
        verifier_fake=True,
    )

    assert agent.model_id == "verified"
    assert agent.base_agent.model_id == "verified_base"
