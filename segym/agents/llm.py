from __future__ import annotations

from segym.agents.base import BaseAgent
from segym.agents.scripted import ScriptedHonestAgent
from segym.types import AgentAction, Observation


class LLMNegotiator(BaseAgent):
    model_id = "llm_interface"

    def act(self, _obs: Observation) -> AgentAction:
        raise RuntimeError("External LLM adapters are intentionally not implemented in the no-API MVP.")


class FakeLLMAgent(ScriptedHonestAgent):
    model_id = "fake_llm"

