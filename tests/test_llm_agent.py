import os

from segym.agents.factory import build_agent
from segym.agents.llm import extract_json_object, normalize_action_payload, observation_prompt
from segym.env import SettlementEthicsEnv
from segym.types import AgentAction


def test_extract_json_object_handles_fenced_json():
    payload = extract_json_object(
        """```json
        {"public_message": "We can offer $100,000.", "offer": 100000}
        ```"""
    )

    assert payload["public_message"] == "We can offer $100,000."
    assert payload["offer"] == 100000


def test_normalize_action_payload_accepts_numeric_offer():
    payload = normalize_action_payload({"public_message": "Offer.", "offer": 100000})
    action = AgentAction.model_validate(payload)

    assert action.offer.type == "monetary"
    assert action.offer.amount_usd == 100000


def test_fake_llm_agent_runs_without_api_key(monkeypatch):
    monkeypatch.setenv("SEGYN_FAKE_MODEL", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/pi_policy_limits_001.yaml")
    obs = env.reset(seed=1)
    agent = build_agent("llm", model_id="fake_configured_llm", model_name="fake-model")

    action = agent.act(obs)

    assert action.public_message
    assert action.offer.amount_usd is not None
    assert action.metadata["llm"]["provider"] == "fake"
    assert action.metadata["llm"]["model"] == "fake-model"


def test_fake_llm_best_of_n_records_candidate_metadata(monkeypatch):
    monkeypatch.setenv("SEGYN_FAKE_MODEL", "1")
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/pi_policy_limits_001.yaml")
    obs = env.reset(seed=1)
    agent = build_agent(
        "llm_best_of_n",
        model_id="fake_llm_best_of_n",
        model_name="fake-model",
        n=3,
        selector="utility_minus_ethics",
    )

    action = agent.act(obs)

    assert action.metadata["best_of_n"]["n_candidates"] == 3
    assert action.metadata["best_of_n"]["selector"] == "utility_minus_ethics"
    assert action.metadata["best_of_n"]["safe_candidate_available"] is True


def test_observation_prompt_contains_hidden_private_case_file(monkeypatch):
    monkeypatch.setenv("SEGYN_FAKE_MODEL", "1")
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/pi_policy_limits_001.yaml")
    obs = env.reset(seed=1)

    prompt = observation_prompt(obs)

    assert "private_case_file" in prompt
    assert "umbrella policy" in prompt
    assert os.environ["SEGYN_FAKE_MODEL"] == "1"
