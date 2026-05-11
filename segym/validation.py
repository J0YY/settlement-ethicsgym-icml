from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from segym.scenario import load_scenario
from segym.types import LABEL_SET, Scenario


REAL_CASE_PATTERNS = [
    re.compile(r"\b\d{2,4}-cv-\d{2,8}\b", re.IGNORECASE),
    re.compile(r"\bNo\.\s*\d{2,4}-[A-Z]{1,4}-\d{2,8}\b", re.IGNORECASE),
]


@dataclass
class ValidationReport:
    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_scenario(scenario: Scenario, path: Path | None = None) -> ValidationReport:
    report = ValidationReport(path=path or Path(scenario.scenario_id))
    fact_ids = {fact.fact_id for fact in scenario.facts}

    for pattern in scenario.forbidden_patterns:
        if pattern.maps_to_fact_id and pattern.maps_to_fact_id not in fact_ids:
            report.errors.append(
                f"{pattern.pattern_id} maps to missing fact {pattern.maps_to_fact_id}"
            )
        if pattern.expected_label not in LABEL_SET:
            report.errors.append(f"{pattern.pattern_id} has unknown label {pattern.expected_label}")

    rv = scenario.reservation_values
    if rv.plaintiff_min_acceptable_usd <= 0 or rv.defense_max_acceptable_usd <= 0:
        report.errors.append("reservation values must be positive")
    if rv.plaintiff_min_acceptable_usd > rv.defense_max_acceptable_usd:
        report.errors.append("plaintiff minimum exceeds defense maximum; no settlement zone")
    if rv.expected_trial_value_usd <= 0:
        report.errors.append("expected trial value must be positive")

    party_roles = {party.role for party in scenario.parties.values()}
    if scenario.agent_role not in party_roles:
        report.errors.append(f"agent_role {scenario.agent_role!r} not present in parties")
    if scenario.opponent_role not in party_roles:
        report.errors.append(f"opponent_role {scenario.opponent_role!r} not present in parties")

    for fact in scenario.facts:
        if fact.truth_value == "true" and fact.unsafe_assertions and fact.materiality != "none":
            report.warnings.append(
                f"{fact.fact_id} is true but has unsafe assertions; check half-truth context"
            )

    for sample in scenario.sample_gold_utterances:
        if sample.label not in LABEL_SET:
            report.errors.append(f"gold utterance has unknown label {sample.label}")

    text_blob = "\n".join(
        [
            scenario.title,
            scenario.public_case_summary,
            scenario.private_case_file_agent,
            scenario.private_case_file_opponent,
        ]
    )
    for regex in REAL_CASE_PATTERNS:
        if regex.search(text_blob):
            report.errors.append("possible real case identifier found")

    if scenario.source_type != "synthetic":
        report.warnings.append("seed scenarios should normally be synthetic")
    if len(scenario.facts) < 3:
        report.warnings.append("scenario has fewer than three facts")
    if len(scenario.sample_gold_utterances) < 3:
        report.warnings.append("scenario has fewer than three gold utterances")
    return report


def validate_path(path: str | Path) -> ValidationReport:
    p = Path(path)
    return validate_scenario(load_scenario(p), p)

