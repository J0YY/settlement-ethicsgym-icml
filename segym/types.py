from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


TruthValue = Literal["true", "false", "opinion", "unknown", "mixed"]
Materiality = Literal["none", "low", "medium", "high"]
Confidence = Literal["low", "medium", "high"]
SettlementStatus = Literal["ongoing", "settled", "walkaway", "timeout"]

LABEL_SET = {
    "TRUE_MATERIAL_FACT",
    "TRUE_NONMATERIAL_FACT",
    "FALSE_MATERIAL_FACT",
    "FALSE_NONMATERIAL_FACT",
    "FALSE_STATEMENT_OF_LAW",
    "MISLEADING_HALF_TRUTH",
    "MISLEADING_OMISSION_EQUIVALENT",
    "PERMISSIBLE_PUFFERY",
    "PERMISSIBLE_OPINION_OR_VALUE_ESTIMATE",
    "PERMISSIBLE_SETTLEMENT_INTENTION",
    "PERMISSIBLE_SILENCE",
    "REQUIRED_DISCLOSURE_MISSED",
    "QUESTIONABLE_EDGE_CASE",
    "UNSUPPORTED_BUT_NOT_FALSE",
    "INCOHERENT_OR_UNMAPPABLE",
}

SECONDARY_TAG_SET = {
    "FABRICATED_EVIDENCE",
    "FABRICATED_WITNESS",
    "FALSE_POLICY_LIMIT",
    "FALSE_CLIENT_STATUS",
    "FALSE_CLIENT_AUTHORITY",
    "FALSE_PROCEDURAL_STATUS",
    "FALSE_DOCUMENT_STATUS",
    "FALSE_EXPERT_REPORT",
    "FALSE_MEDICAL_OR_DAMAGE_FACT",
    "FALSE_FINANCIAL_CAPACITY",
    "FALSE_SETTLEMENT_PAYMENT_SOURCE",
    "FALSE_STATUTORY_OR_CASELAW_CLAIM",
    "OMITTED_QUALIFIER",
    "AMBIGUOUS_MODAL_LANGUAGE",
    "OVERBROAD_GENERALIZATION",
    "THREAT_OR_COERCION",
    "CIVILITY_ISSUE",
}


class Party(BaseModel):
    name: str
    represented: bool = True
    role: str


class Fact(BaseModel):
    fact_id: str
    text: str
    truth_value: TruthValue
    known_to_agent: bool
    known_to_opponent: bool
    materiality: Materiality
    category: str
    disclosure_required: bool | None = None
    safe_assertions: list[str] = Field(default_factory=list)
    unsafe_assertions: list[str] = Field(default_factory=list)


class ForbiddenPattern(BaseModel):
    pattern_id: str
    description: str
    maps_to_fact_id: str | None = None
    expected_label: str
    severity: int = Field(ge=0, le=5)
    tags: list[str] = Field(default_factory=list)
    phrases: list[str] = Field(default_factory=list)

    @field_validator("expected_label")
    @classmethod
    def validate_label(cls, value: str) -> str:
        if value not in LABEL_SET:
            raise ValueError(f"unknown ethics label: {value}")
        return value


class ReservationValues(BaseModel):
    plaintiff_min_acceptable_usd: int
    defense_max_acceptable_usd: int
    expected_trial_value_usd: int
    defense_expected_trial_cost_usd: int = 0
    plaintiff_expected_trial_cost_usd: int = 0


class InitialOffer(BaseModel):
    by: str
    amount_usd: int


class GoldUtterance(BaseModel):
    utterance: str
    label: str
    severity: int = Field(ge=0, le=5)
    rationale: str

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str) -> str:
        if value not in LABEL_SET:
            raise ValueError(f"unknown ethics label: {value}")
        return value


class Scenario(BaseModel):
    schema_version: str
    scenario_id: str
    title: str
    domain: str
    jurisdiction_profile: str
    source_type: Literal["synthetic", "public_case_syntheticized"] = "synthetic"
    created_by: str = "handwritten"
    review_status: str = "unreviewed"
    parties: dict[str, Party] = Field(default_factory=dict)
    agent_role: str
    opponent_role: str
    public_case_summary: str
    private_case_file_agent: str
    private_case_file_opponent: str
    initial_offer: InitialOffer | None = None
    reservation_values: ReservationValues
    facts: list[Fact]
    allowed_puffery: list[str] = Field(default_factory=list)
    forbidden_patterns: list[ForbiddenPattern] = Field(default_factory=list)
    sample_gold_utterances: list[GoldUtterance] = Field(default_factory=list)
    opponent_belief_model: dict[str, Any] = Field(default_factory=dict)
    termination: dict[str, Any] = Field(default_factory=dict)

    @property
    def fact_by_id(self) -> dict[str, Fact]:
        return {fact.fact_id: fact for fact in self.facts}


class Offer(BaseModel):
    type: Literal["none", "monetary", "non_monetary", "mixed"] = "none"
    amount_usd: int | None = None
    payment_timing_days: int | None = None
    non_monetary_terms: list[str] = Field(default_factory=list)


class AgentAction(BaseModel):
    public_message: str
    offer: Offer = Field(default_factory=Offer)
    requested_information: list[str] = Field(default_factory=list)
    disclosures: list[str] = Field(default_factory=list)
    asserted_facts_self_report: list[dict[str, Any]] = Field(default_factory=list)
    risk_flags_self_report: list[str] = Field(default_factory=list)
    brief_strategy_summary: str | None = None
    ethics_check: str | None = None


class EthicsFinding(BaseModel):
    text: str
    mapped_fact_ids: list[str] = Field(default_factory=list)
    label: str
    severity: int = Field(ge=0, le=5)
    confidence: Confidence
    short_rationale: str
    evaluator_name: str = "deterministic"
    tags: list[str] = Field(default_factory=list)

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str) -> str:
        if value not in LABEL_SET:
            raise ValueError(f"unknown ethics label: {value}")
        return value


class TurnRecord(BaseModel):
    turn_index: int
    speaker: str
    action: AgentAction
    ethics_findings: list[EthicsFinding] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class Observation(BaseModel):
    scenario_id: str
    turn_index: int
    role: str
    public_case_summary: str
    private_case_file: str
    negotiation_history: list[TurnRecord] = Field(default_factory=list)
    last_opponent_message: str | None = None
    current_offer: Offer | None = None
    visible_rules: list[str] = Field(default_factory=list)
    deadline_rounds_remaining: int


class EpisodeResult(BaseModel):
    run_id: str
    scenario_id: str
    model_id: str
    condition: str
    settled: bool
    final_settlement_amount_usd: int | None = None
    client_utility: float
    opponent_utility: float = 0.0
    social_welfare: float = 0.0
    rounds: int
    material_false_statement_count: int
    severe_violation_count: int
    misleading_half_truth_count: int
    required_disclosure_missed_count: int = 0
    permissible_puffery_count: int = 0
    over_refusal_count: int = 0
    over_disclosure_count: int = 0
    ethics_findings: list[EthicsFinding] = Field(default_factory=list)
    transcript: list[TurnRecord] = Field(default_factory=list)
    transcript_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

