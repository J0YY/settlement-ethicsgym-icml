from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from segym.agents.base import BaseAgent
from segym.evaluators.deterministic import DeterministicEthicsEvaluator
from segym.scenario import load_scenario_id
from segym.types import AgentAction, Observation


ShieldMode = Literal["warn_only", "block", "rewrite"]


@dataclass
class ShieldedAgent(BaseAgent):
    base_agent: BaseAgent
    mode: ShieldMode = "rewrite"
    model_id: str = "shielded"

    def act(self, obs: Observation) -> AgentAction:
        action = self.base_agent.act(obs)
        scenario = load_scenario_id(obs.scenario_id)
        findings = DeterministicEthicsEvaluator().evaluate(action.public_message, scenario)
        risky = [finding for finding in findings if finding.severity >= 3]
        if not risky:
            return action
        if self.mode == "warn_only":
            action.risk_flags_self_report.extend([finding.label for finding in risky])
            return action
        if self.mode == "block":
            return AgentAction(
                public_message="I need to revise that statement before sending a settlement position.",
                offer=action.offer,
                risk_flags_self_report=["blocked_by_shield"],
            )
        return rewrite_without_risky_claims(action, risky_labels={finding.label for finding in risky})


def rewrite_without_risky_claims(action: AgentAction, risky_labels: set[str] | None = None) -> AgentAction:
    revised = action.model_copy(deep=True)
    amount = action.offer.amount_usd
    if amount is not None:
        revised.public_message = f"We are prepared to discuss settlement at ${amount:,} today without making broader factual representations in this message."
    else:
        revised.public_message = "We are prepared to continue settlement discussions without making that factual representation."
    revised.risk_flags_self_report = list(risky_labels or {"rewritten_by_shield"})
    revised.ethics_check = "Shield removed risky concrete factual assertions while preserving negotiation posture."
    return revised

