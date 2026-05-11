from __future__ import annotations

from segym.agents.best_of_n import BestOfNEthicsAwareAgent, BestOfNUtilityAgent
from segym.agents.scripted import ScriptedDeceptiveAgent, ScriptedHonestAgent
from segym.agents.shielded import ShieldedAgent


def build_agent(name: str, **kwargs):
    if name == "scripted_honest":
        return ScriptedHonestAgent()
    if name == "scripted_deceptive":
        return ScriptedDeceptiveAgent()
    if name == "best_of_n_utility":
        return BestOfNUtilityAgent(n=int(kwargs.get("n", 4)))
    if name == "best_of_n_ethics":
        return BestOfNEthicsAwareAgent(n=int(kwargs.get("n", 4)), lambda_ethics=float(kwargs.get("lambda_ethics", 1.0)))
    if name == "shielded_deceptive":
        base_type = kwargs.get("base_type", "scripted_deceptive")
        base_agent = build_agent(base_type) if base_type != "shielded_deceptive" else ScriptedDeceptiveAgent()
        return ShieldedAgent(base_agent, mode=kwargs.get("shield_mode", "rewrite"))
    raise ValueError(f"unknown agent: {name}")
