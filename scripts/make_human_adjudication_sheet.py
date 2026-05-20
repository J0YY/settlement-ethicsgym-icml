from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from segym.scenario import load_scenario_id


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def scenario_facts(scenario_id: str) -> str:
    scenario = load_scenario_id(scenario_id)
    facts = []
    for fact in scenario.facts:
        facts.append(
            {
                "fact_id": fact.fact_id,
                "text": fact.text,
                "truth_value": fact.truth_value,
                "known_to_agent": fact.known_to_agent,
                "known_to_opponent": fact.known_to_opponent,
                "materiality": fact.materiality,
                "category": fact.category,
                "disclosure_required": fact.disclosure_required,
            }
        )
    return json.dumps(facts, sort_keys=True)


def make_sheet(sample_path: Path, predictions_path: Path, out: Path, *, flagged_only: bool = True) -> int:
    sample = pd.read_csv(sample_path).fillna("")
    predictions = pd.read_csv(predictions_path).fillna("")
    prediction_columns = [
        "audit_id",
        "deterministic_label",
        "deterministic_severity",
        "deterministic_violation",
        "deterministic_findings_json",
        "llm_judge_label",
        "llm_judge_severity",
        "llm_judge_violation",
        "llm_judge_findings_json",
    ]
    merged = sample.merge(
        predictions[[column for column in prediction_columns if column in predictions.columns]],
        on="audit_id",
        how="left",
    ).fillna("")
    if flagged_only:
        merged = merged[merged["llm_judge_violation"].map(bool_value)].copy()
    merged["scenario_facts_json"] = [scenario_facts(str(value)) for value in merged["scenario_id"]]
    merged["human_adjudicated_label"] = ""
    merged["human_adjudicated_severity"] = ""
    merged["human_violation"] = ""
    merged["human_confidence"] = ""
    merged["human_reviewer_role"] = ""
    merged["human_adjudication_notes"] = ""
    merged["human_review_date"] = ""
    columns = [
        "audit_id",
        "source_type",
        "scenario_id",
        "model_id",
        "condition",
        "turn_index",
        "candidate_index",
        "selected",
        "public_message",
        "scenario_facts_json",
        "deterministic_label",
        "deterministic_severity",
        "deterministic_violation",
        "deterministic_findings_json",
        "llm_judge_label",
        "llm_judge_severity",
        "llm_judge_violation",
        "llm_judge_findings_json",
        "human_adjudicated_label",
        "human_adjudicated_severity",
        "human_violation",
        "human_confidence",
        "human_reviewer_role",
        "human_adjudication_notes",
        "human_review_date",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    merged[[column for column in columns if column in merged.columns]].to_csv(out, index=False)
    return len(merged)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sample", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--include-all", action="store_true")
    args = parser.parse_args()

    n_rows = make_sheet(
        Path(args.audit_sample),
        Path(args.predictions),
        Path(args.out),
        flagged_only=not args.include_all,
    )
    print(f"Wrote {n_rows} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
