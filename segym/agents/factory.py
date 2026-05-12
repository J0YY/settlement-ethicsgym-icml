from __future__ import annotations

from segym.agents.best_of_n import BestOfNEthicsAwareAgent, BestOfNUtilityAgent
from segym.agents.llm import FakeLLMAgent, LLMBestOfNAgent, LLMNegotiator
from segym.agents.scripted import ScriptedDeceptiveAgent, ScriptedHonestAgent
from segym.agents.shielded import ShieldedAgent


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
            n=int(kwargs.get("n", 4)),
            selector=kwargs.get("selector", "utility_only"),
            lambda_ethics=float(kwargs.get("lambda_ethics", 1.0)),
        )
    if name == "best_of_n_utility":
        return BestOfNUtilityAgent(n=int(kwargs.get("n", 4)))
    if name == "best_of_n_ethics":
        return BestOfNEthicsAwareAgent(n=int(kwargs.get("n", 4)), lambda_ethics=float(kwargs.get("lambda_ethics", 1.0)))
    if name == "shielded_deceptive":
        base_type = kwargs.get("base_type", "scripted_deceptive")
        base_agent = build_agent(base_type) if base_type != "shielded_deceptive" else ScriptedDeceptiveAgent()
        return ShieldedAgent(base_agent, mode=kwargs.get("shield_mode", "rewrite"))
    raise ValueError(f"unknown agent: {name}")
