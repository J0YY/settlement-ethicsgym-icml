from __future__ import annotations

from dataclasses import dataclass

from segym.agents.base import BaseAgent
from segym.agents.scripted import ScriptedDeceptiveAgent, ScriptedHonestAgent
from segym.evaluators.deterministic import DeterministicEthicsEvaluator
from segym.rewards import client_utility
from segym.scenario import load_scenario_id
from segym.types import AgentAction, Observation


def estimated_utility(action: AgentAction, obs: Observation) -> float:
    scenario = load_scenario_id(obs.scenario_id)
    base = client_utility(scenario, action.offer.amount_usd, obs.role)
    text = action.public_message.lower()
    leverage_terms = ["only", "eyewitness", "video", "records show", "served", "limitations period"]
    return base + (0.35 if any(term in text for term in leverage_terms) else 0.0)


@dataclass
class BestOfNUtilityAgent(BaseAgent):
    n: int = 4
    model_id: str = "best_of_n_utility"

    def act(self, obs: Observation) -> AgentAction:
        candidates = self._candidates(obs)
        return max(candidates[: self.n], key=lambda action: estimated_utility(action, obs))

    def _candidates(self, obs: Observation) -> list[AgentAction]:
        honest = ScriptedHonestAgent().act(obs)
        deceptive = ScriptedDeceptiveAgent().act(obs)
        softer = honest.model_copy(deep=True)
        softer.public_message = softer.public_message.replace("resolve this matter", "continue productive discussions")
        return [honest, softer, deceptive, honest]


@dataclass
class BestOfNEthicsAwareAgent(BestOfNUtilityAgent):
    lambda_ethics: float = 1.0
    model_id: str = "best_of_n_ethics"

    def act(self, obs: Observation) -> AgentAction:
        scenario = load_scenario_id(obs.scenario_id)
        evaluator = DeterministicEthicsEvaluator()
        candidates = self._candidates(obs)[: self.n]

        def score(action: AgentAction) -> float:
            findings = evaluator.evaluate(action.public_message, scenario)
            penalty = sum(1 for finding in findings if finding.severity >= 3)
            return estimated_utility(action, obs) - self.lambda_ethics * penalty

        return max(candidates, key=score)
