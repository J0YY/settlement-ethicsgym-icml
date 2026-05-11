from segym.agents import ScriptedDeceptiveAgent, ScriptedHonestAgent
from segym.env import SettlementEthicsEnv


def test_env_runs_to_timeout_or_settlement_with_scripted_agent():
    env = SettlementEthicsEnv.from_path(
        "data/scenarios/seed/pi_policy_limits_001.yaml",
        config={"max_rounds": 2, "model_id": "scripted_honest", "condition": "test"},
    )
    obs = env.reset(seed=1)
    done = False
    while not done:
        obs, _reward, done, _info = env.step(ScriptedHonestAgent().act(obs))
    result = env.result()
    assert result.rounds >= 1
    assert result.scenario_id == "pi_policy_limits_001"


def test_env_settles_when_offer_crosses_threshold():
    env = SettlementEthicsEnv.from_path(
        "data/scenarios/seed/pi_policy_limits_001.yaml",
        config={"max_rounds": 6, "model_id": "scripted_honest", "condition": "test"},
    )
    obs = env.reset(seed=1)
    action = ScriptedHonestAgent().act(obs)
    action.offer.amount_usd = 130000
    _obs, _reward, done, _info = env.step(action)
    assert done
    assert env.result().settled


def test_opponent_belief_updates_on_false_coverage_claim():
    env = SettlementEthicsEnv.from_path(
        "data/scenarios/seed/pi_policy_limits_001.yaml",
        config={"max_rounds": 1, "model_id": "scripted_deceptive", "condition": "test"},
    )
    obs = env.reset(seed=1)
    _obs, _reward, _done, info = env.step(ScriptedDeceptiveAgent().act(obs))
    assert info["opponent_reliance_count"] >= 1
    assert info["opponent_belief_state"]["available_coverage"] == 50000


def test_episode_result_serializes():
    env = SettlementEthicsEnv.from_path(
        "data/scenarios/seed/pi_policy_limits_001.yaml",
        config={"max_rounds": 1, "model_id": "scripted_honest", "condition": "test"},
    )
    obs = env.reset(seed=1)
    env.step(ScriptedHonestAgent().act(obs))
    assert env.result().model_dump(mode="json")

