from __future__ import annotations

from abc import ABC, abstractmethod

from segym.types import AgentAction, Observation


class BaseAgent(ABC):
    model_id = "base"

    @abstractmethod
    def act(self, obs: Observation) -> AgentAction:
        raise NotImplementedError

