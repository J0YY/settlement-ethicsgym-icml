from __future__ import annotations

from segym.agents.best_of_n import BestOfNEthicsAwareAgent, BestOfNUtilityAgent
from segym.agents.llm import FakeLLMAgent, LLMBestOfNAgent, LLMNegotiator
from segym.agents.scripted import ScriptedDeceptiveAgent, ScriptedHonestAgent
from segym.agents.shielded import LLMVerifiedShieldedAgent, ShieldedAgent


def build_agent(name: str, **kwargs):
    if name == "scripted_honest":
        return ScriptedHonestAgent()
    if name == "scripted_deceptive":
        return ScriptedDeceptiveAgent()
    if name == "fake_llm":
        return FakeLLMAgent(model_id=kwargs.get("model_id", "fake_llm"))
    if name == "llm":
        return LLMNegotiator(
            model_id=kwargs.get("model_id", "llm"),
            provider=kwargs.get("provider", "openai_compatible"),
            model_name=kwargs.get("model_name", "gpt-4.1-mini"),
            system_prompt_path=kwargs.get("system_prompt_path"),
            temperature=float(kwargs.get("temperature", 0.2)),
            max_tokens=int(kwargs.get("max_tokens", 800)),
            api_key_env=kwargs.get("api_key_env", "OPENAI_API_KEY"),
            base_url=kwargs.get("base_url", "https://api.openai.com/v1/chat/completions"),
            fake=bool(kwargs.get("fake", False)),
            max_parse_retries=int(kwargs.get("max_parse_retries", 1)),
            max_request_retries=int(kwargs.get("max_request_retries", 4)),
        )
    if name == "llm_best_of_n":
        return LLMBestOfNAgent(
            model_id=kwargs.get("model_id", "llm_best_of_n"),
            provider=kwargs.get("provider", "openai_compatible"),
            model_name=kwargs.get("model_name", "gpt-4.1-mini"),
            system_prompt_path=kwargs.get("system_prompt_path"),
            temperature=float(kwargs.get("temperature", 0.2)),
            max_tokens=int(kwargs.get("max_tokens", 800)),
            api_key_env=kwargs.get("api_key_env", "OPENAI_API_KEY"),
            base_url=kwargs.get("base_url", "https://api.openai.com/v1/chat/completions"),
            fake=bool(kwargs.get("fake", False)),
            max_parse_retries=int(kwargs.get("max_parse_retries", 1)),
            max_request_retries=int(kwargs.get("max_request_retries", 4)),
            n=int(kwargs.get("n", 4)),
            selector=kwargs.get("selector", "utility_only"),
            lambda_ethics=float(kwargs.get("lambda_ethics", 1.0)),
        )
    if name == "best_of_n_utility":
        return BestOfNUtilityAgent(n=int(kwargs.get("n", 4)))
    if name == "best_of_n_ethics":
        return BestOfNEthicsAwareAgent(n=int(kwargs.get("n", 4)), lambda_ethics=float(kwargs.get("lambda_ethics", 1.0)))
    if name in {"shielded", "shielded_deceptive"}:
        base_type = kwargs.get("base_type", "scripted_deceptive")
        if base_type in {"shielded", "shielded_deceptive"}:
            base_agent = ScriptedDeceptiveAgent()
        else:
            base_agent = build_agent(
                base_type,
                model_id=kwargs.get("base_model_id", f"{kwargs.get('model_id', 'shielded')}_base"),
                provider=kwargs.get("provider", "openai_compatible"),
                model_name=kwargs.get("model_name", "gpt-4.1-mini"),
                system_prompt_path=kwargs.get("system_prompt_path"),
                temperature=kwargs.get("temperature", 0.2),
                max_tokens=kwargs.get("max_tokens", 800),
                api_key_env=kwargs.get("api_key_env", "OPENAI_API_KEY"),
                base_url=kwargs.get("base_url", "https://api.openai.com/v1/chat/completions"),
                fake=kwargs.get("fake", False),
                max_parse_retries=kwargs.get("max_parse_retries", 1),
                max_request_retries=kwargs.get("max_request_retries", 4),
                n=kwargs.get("n", 4),
                selector=kwargs.get("selector", "utility_only"),
                lambda_ethics=kwargs.get("lambda_ethics", 1.0),
            )
        return ShieldedAgent(base_agent, mode=kwargs.get("shield_mode", "rewrite"), model_id=kwargs.get("model_id", "shielded"))
    if name in {"llm_verified_shielded", "verified_shielded"}:
        base_agent = build_agent(
            kwargs.get("base_type", "llm"),
            model_id=kwargs.get("base_model_id", f"{kwargs.get('model_id', 'verified_shielded')}_base"),
            provider=kwargs.get("provider", "openai_compatible"),
            model_name=kwargs.get("model_name", "gpt-4.1-mini"),
            system_prompt_path=kwargs.get("system_prompt_path"),
            temperature=kwargs.get("temperature", 0.2),
            max_tokens=kwargs.get("max_tokens", 800),
            api_key_env=kwargs.get("api_key_env", "OPENAI_API_KEY"),
            base_url=kwargs.get("base_url", "https://api.openai.com/v1/chat/completions"),
            fake=kwargs.get("fake", False),
            max_parse_retries=kwargs.get("max_parse_retries", 1),
            max_request_retries=kwargs.get("max_request_retries", 4),
            n=kwargs.get("n", 4),
            selector=kwargs.get("selector", "utility_only"),
            lambda_ethics=kwargs.get("lambda_ethics", 1.0),
        )
        return LLMVerifiedShieldedAgent(
            base_agent=base_agent,
            mode=kwargs.get("shield_mode", "rewrite"),
            model_id=kwargs.get("model_id", "llm_verified_shielded"),
            verifier_provider=kwargs.get("verifier_provider", "openai_compatible"),
            verifier_model_name=kwargs.get("verifier_model_name", "gpt-4.1"),
            verifier_api_key_env=kwargs.get("verifier_api_key_env", kwargs.get("api_key_env", "OPENAI_API_KEY")),
            verifier_base_url=kwargs.get("verifier_base_url", kwargs.get("base_url", "https://api.openai.com/v1/chat/completions")),
            verifier_fake=bool(kwargs.get("verifier_fake", kwargs.get("fake", False))),
        )
    raise ValueError(f"unknown agent: {name}")
