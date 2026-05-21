import json
import os
import urllib.error

from segym.agents.factory import build_agent
from segym.agents.llm import (
    AnthropicMessagesClient,
    OpenAICompatibleClient,
    extract_json_object,
    normalize_action_payload,
    observation_prompt,
)
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


def test_normalize_action_payload_accepts_string_asserted_facts():
    payload = normalize_action_payload(
        {
            "public_message": "Offer.",
            "offer": 100000,
            "asserted_facts_self_report": ["The primary policy is $50,000."],
        }
    )
    action = AgentAction.model_validate(payload)

    assert action.asserted_facts_self_report == [{"text": "The primary policy is $50,000."}]


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


def test_openai_client_retries_transient_request_failure(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"choices": [{"message": {"content": "{\\"ok\\": true}"}}]}'

    def urlopen(request, timeout):
        calls.append((request, timeout))
        if len(calls) == 1:
            raise urllib.error.URLError("timed out")
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    client = OpenAICompatibleClient(model="test-model", max_request_retries=1, retry_base_seconds=0)

    assert client.complete("system", "user") == '{"ok": true}'
    assert len(calls) == 2


def test_openai_client_does_not_retry_nontransient_http_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls = []

    def urlopen(request, timeout):
        calls.append((request, timeout))
        raise urllib.error.HTTPError(
            request.full_url,
            400,
            "bad request",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    client = OpenAICompatibleClient(model="test-model", max_request_retries=3, retry_base_seconds=0)

    try:
        client.complete("system", "user")
    except Exception as exc:
        assert "HTTP 400" in str(exc)
    else:
        raise AssertionError("expected nontransient HTTP error")
    assert len(calls) == 1


def test_anthropic_client_uses_messages_api_and_extracts_text(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"content": [{"type": "text", "text": "{\\"ok\\": true}"}]}'

    def urlopen(request, timeout):
        calls.append((request, timeout, json.loads(request.data.decode("utf-8"))))
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    client = AnthropicMessagesClient(model="claude-test", max_request_retries=0)

    assert client.complete("system", "user") == '{"ok": true}'
    request, timeout, body = calls[0]
    assert timeout == 60
    assert request.headers["X-api-key"] == "test-key"
    assert request.headers["Anthropic-version"] == "2023-06-01"
    assert body["model"] == "claude-test"
    assert body["system"] == "system"
    assert body["messages"] == [{"role": "user", "content": "user"}]


def test_llm_agent_retries_and_logs_parse_failure(monkeypatch):
    monkeypatch.delenv("SEGYN_FAKE_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls = []

    def complete(self, system_prompt, user_prompt):
        calls.append(user_prompt)
        if len(calls) == 1:
            return "not json"
        return '{"public_message": "We can offer $100,000.", "offer": 100000}'

    monkeypatch.setattr(OpenAICompatibleClient, "complete", complete)
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/pi_policy_limits_001.yaml")
    agent = build_agent("llm", model_id="parse_retry_llm", max_parse_retries=1)

    action = agent.act(env.reset(seed=1))

    assert action.public_message == "We can offer $100,000."
    assert action.metadata["llm"]["parse_failed"] is False
    assert action.metadata["llm"]["parse_failure_count"] == 1
    assert action.metadata["llm"]["parse_failures"][0]["raw_text"] == "not json"
    assert "previous response could not be parsed" in calls[1]


def test_llm_agent_returns_safe_fallback_after_parse_failures(monkeypatch):
    monkeypatch.delenv("SEGYN_FAKE_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def complete(self, system_prompt, user_prompt):
        return "not json"

    monkeypatch.setattr(OpenAICompatibleClient, "complete", complete)
    env = SettlementEthicsEnv.from_path("data/scenarios/seed/pi_policy_limits_001.yaml")
    obs = env.reset(seed=1)
    agent = build_agent("llm", model_id="parse_failure_llm", max_parse_retries=0)

    action = agent.act(obs)
    env.step(action)

    assert action.offer.type == "none"
    assert action.metadata["llm"]["parse_failed"] is True
    assert action.metadata["llm"]["parse_failure_count"] == 1
    assert "llm_parse_failure" in action.risk_flags_self_report
    assert env.result().metadata["llm_parse_failed"] is True
    assert env.result().metadata["llm_parse_failure_count"] == 1
