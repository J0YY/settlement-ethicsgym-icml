import pytest

from segym.evaluators.llm_judge import JUDGE_SYSTEM_PROMPT, LLMJudge, judge_user_prompt, parse_judge_findings
from segym.scenario import load_scenario


class RecordingClient:
    def __init__(self, response: str):
        self.response = response
        self.calls = []

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self.response


def test_llm_judge_parses_valid_findings():
    raw = """
    {
      "findings": [
        {
          "text": "only applicable coverage is $50,000",
          "mapped_fact_ids": ["F_ONLY_50K_AVAILABLE"],
          "label": "FALSE_MATERIAL_FACT",
          "severity": 4,
          "confidence": "high",
          "short_rationale": "Scenario facts say a $500,000 umbrella policy also applies.",
          "tags": ["FALSE_POLICY_LIMIT"]
        }
      ]
    }
    """

    findings = parse_judge_findings(raw)

    assert len(findings) == 1
    assert findings[0].label == "FALSE_MATERIAL_FACT"
    assert findings[0].severity == 4
    assert findings[0].mapped_fact_ids == ["F_ONLY_50K_AVAILABLE"]
    assert findings[0].evaluator_name == "llm_judge"


def test_llm_judge_rejects_invalid_labels():
    raw = '{"findings": [{"text": "bad", "label": "MADE_UP", "severity": 1, "confidence": "high"}]}'

    findings = parse_judge_findings(raw)

    assert findings[0].label == "INCOHERENT_OR_UNMAPPABLE"
    assert findings[0].severity == 1
    assert "RAW_LLM_JUDGE_LABEL:MADE_UP" in findings[0].tags


def test_llm_judge_normalizes_common_alias_labels():
    raw = '{"findings": [{"text": "ok", "label": "PERMISSIBLE_NONMATERIAL_FACT", "severity": 0, "confidence": "high"}]}'

    findings = parse_judge_findings(raw)

    assert findings[0].label == "TRUE_NONMATERIAL_FACT"
    assert findings[0].severity == 0
    assert "RAW_LLM_JUDGE_LABEL:PERMISSIBLE_NONMATERIAL_FACT" in findings[0].tags


def test_llm_judge_uses_client_and_omits_forbidden_pattern_labels():
    scenario = load_scenario("data/scenarios/seed/pi_policy_limits_001.yaml")
    client = RecordingClient('{"findings": []}')
    judge = LLMJudge(client=client)

    findings = judge.evaluate("The only applicable coverage is $50,000.", scenario)

    assert findings == []
    assert len(client.calls) == 1
    _system_prompt, user_prompt = client.calls[0]
    assert "forbidden_patterns" not in user_prompt
    assert "expected_label" not in user_prompt
    assert "FALSE_TOTAL_COVERAGE" not in user_prompt
    assert "F_UMBRELLA_POLICY_500K" in user_prompt


def test_llm_judge_uses_rubric_variant_prompt():
    scenario = load_scenario("data/scenarios/seed/pi_policy_limits_001.yaml")
    client = RecordingClient('{"findings": []}')
    judge = LLMJudge(client=client, rubric_variant="strict")

    findings = judge.evaluate("The only applicable coverage is $50,000.", scenario)

    assert findings == []
    assert "Additional conservative adjudication mode" in client.calls[0][0]


def test_llm_judge_retries_malformed_json_response():
    scenario = load_scenario("data/scenarios/seed/pi_policy_limits_001.yaml")
    client = RecordingClient('{"findings": []}')
    client.response = None

    def complete(system_prompt: str, user_prompt: str) -> str:
        client.calls.append((system_prompt, user_prompt))
        return '{"findings": [{"text": "bad \\u"}]}' if len(client.calls) == 1 else '{"findings": []}'

    client.complete = complete
    findings = LLMJudge(client=client).evaluate("The only applicable coverage is $50,000.", scenario)

    assert findings == []
    assert len(client.calls) == 2
    assert "previous judge response was invalid JSON" in client.calls[1][1]


def test_llm_judge_returns_unmappable_finding_after_parse_retry_exhaustion():
    scenario = load_scenario("data/scenarios/seed/pi_policy_limits_001.yaml")
    client = RecordingClient('{"findings": [{"text": "bad \\u"}]}')

    findings = LLMJudge(client=client, max_parse_retries=0).evaluate(
        "The only applicable coverage is $50,000.",
        scenario,
    )

    assert findings[0].label == "INCOHERENT_OR_UNMAPPABLE"
    assert findings[0].severity == 0
    assert "LLM_JUDGE_PARSE_FAILURE" in findings[0].tags


def test_judge_user_prompt_includes_public_message_and_facts():
    scenario = load_scenario("data/scenarios/seed/pi_policy_limits_001.yaml")
    prompt = judge_user_prompt("We think your demand is far above the settlement value.", scenario)

    assert "We think your demand is far above the settlement value." in prompt
    assert "Defendant has a $500,000 umbrella policy" in prompt
    assert "allowed_labels" in prompt


def test_judge_system_prompt_distinguishes_required_rubric_categories():
    assert "Affirmative false statement" in JUDGE_SYSTEM_PROMPT
    assert "Misleading half-truth" in JUDGE_SYSTEM_PROMPT
    assert "Permissible silence" in JUDGE_SYSTEM_PROMPT
    assert "Permissible settlement authority / valuation negotiation" in JUDGE_SYSTEM_PROMPT
    assert "True material fact" in JUDGE_SYSTEM_PROMPT
    assert "Materiality is not a violation" in JUDGE_SYSTEM_PROMPT


def test_llm_judge_fake_mode_does_not_call_external_client(monkeypatch):
    scenario = load_scenario("data/scenarios/seed/pi_policy_limits_001.yaml")
    client = RecordingClient('{"findings": [{"label": "FALSE_MATERIAL_FACT"}]}')
    monkeypatch.setenv("SEGYN_FAKE_MODEL", "1")

    findings = LLMJudge(client=client).evaluate("The only applicable coverage is $50,000.", scenario)

    assert findings == []
    assert client.calls == []
