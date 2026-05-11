from __future__ import annotations

from segym.evaluators.deterministic import DeterministicEthicsEvaluator
from segym.types import EthicsFinding, Scenario


class EthicsEnsemble:
    def __init__(self) -> None:
        self.deterministic = DeterministicEthicsEvaluator()

    def evaluate(self, message: str, scenario: Scenario) -> list[EthicsFinding]:
        return self.deterministic.evaluate(message, scenario)

