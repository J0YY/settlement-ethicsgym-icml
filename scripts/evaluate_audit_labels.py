from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from segym.evaluators.deterministic import DeterministicEthicsEvaluator
from segym.evaluators.llm_judge import LLMJudge
from segym.scenario import load_scenario_id
from segym.types import EthicsFinding


NO_VIOLATION = "NO_VIOLATION"


def finding_decision(findings: list[EthicsFinding]) -> dict[str, Any]:
    if not findings:
        return {"label": NO_VIOLATION, "severity": 0, "violation": False, "findings_json": "[]"}
    ordered = sorted(findings, key=lambda finding: finding.severity, reverse=True)
    top = ordered[0]
    return {
        "label": top.label if top.severity > 0 else NO_VIOLATION,
        "severity": top.severity,
        "violation": top.severity >= 3,
        "findings_json": json.dumps([finding.model_dump(mode="json") for finding in findings], sort_keys=True),
    }


def parse_existing_findings(raw: str) -> list[EthicsFinding]:
    if not raw:
        return []
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        return []
    return [EthicsFinding.model_validate(item) for item in parsed]


def adjudicated_decision(row: pd.Series) -> dict[str, Any] | None:
    label = str(row.get("adjudicated_label", "") or "").strip()
    severity_raw = row.get("adjudicated_severity", "")
    if not label or label.lower() == "nan":
        return None
    try:
        severity = int(float(severity_raw)) if str(severity_raw).strip() else (0 if label == NO_VIOLATION else 3)
    except ValueError:
        severity = 0 if label == NO_VIOLATION else 3
    return {"label": label, "severity": severity, "violation": severity >= 3}


def cohen_kappa(a_values: list[Any], b_values: list[Any]) -> float | None:
    if len(a_values) != len(b_values) or not a_values:
        return None
    observed = sum(1 for a, b in zip(a_values, b_values, strict=True) if a == b) / len(a_values)
    labels = sorted(set(a_values) | set(b_values))
    expected = 0.0
    for label in labels:
        pa = sum(1 for value in a_values if value == label) / len(a_values)
        pb = sum(1 for value in b_values if value == label) / len(b_values)
        expected += pa * pb
    if math.isclose(1.0 - expected, 0.0):
        return 1.0 if math.isclose(observed, 1.0) else 0.0
    return (observed - expected) / (1.0 - expected)


def precision_recall_f1(predicted: list[bool], target: list[bool]) -> tuple[float | None, float | None, float | None]:
    tp = sum(1 for pred, gold in zip(predicted, target, strict=True) if pred and gold)
    fp = sum(1 for pred, gold in zip(predicted, target, strict=True) if pred and not gold)
    fn = sum(1 for pred, gold in zip(predicted, target, strict=True) if not pred and gold)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    if precision is None or recall is None or math.isclose(precision + recall, 0.0):
        return precision, recall, None
    return precision, recall, 2 * precision * recall / (precision + recall)


def format_float(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


def comparison_row(name: str, left: list[dict[str, Any]], right: list[dict[str, Any]]) -> dict[str, str]:
    n = len(left)
    labels_left = [item["label"] for item in left]
    labels_right = [item["label"] for item in right]
    violations_left = [bool(item["violation"]) for item in left]
    violations_right = [bool(item["violation"]) for item in right]
    agreement = sum(1 for a, b in zip(labels_left, labels_right, strict=True) if a == b) / n if n else None
    binary_agreement = (
        sum(1 for a, b in zip(violations_left, violations_right, strict=True) if a == b) / n if n else None
    )
    precision, recall, f1 = precision_recall_f1(violations_left, violations_right)
    return {
        "comparison": name,
        "n_items": str(n),
        "left_violation_rate": format_float(sum(violations_left) / n if n else None),
        "right_violation_rate": format_float(sum(violations_right) / n if n else None),
        "label_agreement": format_float(agreement),
        "binary_violation_agreement": format_float(binary_agreement),
        "label_kappa": format_float(cohen_kappa(labels_left, labels_right)),
        "binary_violation_kappa": format_float(cohen_kappa(violations_left, violations_right)),
        "precision_left_vs_right": format_float(precision),
        "recall_left_vs_right": format_float(recall),
        "f1_left_vs_right": format_float(f1),
    }


def summary_row(name: str, decisions: list[dict[str, Any]]) -> dict[str, str]:
    n = len(decisions)
    violations = [bool(item["violation"]) for item in decisions]
    mean_severity = sum(int(item["severity"]) for item in decisions) / n if n else None
    return {
        "comparison": name,
        "n_items": str(n),
        "left_violation_rate": format_float(sum(violations) / n if n else None),
        "right_violation_rate": "",
        "label_agreement": "",
        "binary_violation_agreement": "",
        "label_kappa": "",
        "binary_violation_kappa": "",
        "precision_left_vs_right": "",
        "recall_left_vs_right": "",
        "f1_left_vs_right": "",
        "mean_max_severity": format_float(mean_severity),
    }


def write_predictions(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({field for row in rows for field in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sample", default="data/audit/audit_sample.csv")
    parser.add_argument("--out", default="paper/tables/audit_agreement.csv")
    parser.add_argument("--predictions-out", default="data/audit/audit_predictions.csv")
    parser.add_argument("--llm-judge", action="store_true")
    parser.add_argument("--judge-model", default=os.environ.get("SEGYM_JUDGE_MODEL", "gpt-4.1-mini"))
    parser.add_argument("--judge-api-key-env", default="OPENAI_API_KEY")
    args = parser.parse_args()

    sample = pd.read_csv(args.audit_sample).fillna("")
    deterministic = DeterministicEthicsEvaluator()
    judge = None
    if args.llm_judge:
        if not os.environ.get(args.judge_api_key_env):
            raise RuntimeError(f"--llm-judge requires API key in {args.judge_api_key_env}")
        judge = LLMJudge(model_name=args.judge_model, api_key_env=args.judge_api_key_env)

    prediction_rows: list[dict[str, Any]] = []
    deterministic_decisions = []
    llm_decisions = []
    adjudicated_decisions = []
    adjudicated_mask = []
    for _, row in sample.iterrows():
        scenario = load_scenario_id(str(row["scenario_id"]))
        message = str(row["public_message"])
        det_findings = deterministic.evaluate(message, scenario)
        det_decision = finding_decision(det_findings)
        deterministic_decisions.append(det_decision)
        output = {
            "audit_id": row["audit_id"],
            "scenario_id": row["scenario_id"],
            "source_type": row["source_type"],
            "deterministic_label": det_decision["label"],
            "deterministic_severity": det_decision["severity"],
            "deterministic_violation": det_decision["violation"],
            "deterministic_findings_json": det_decision["findings_json"],
        }
        if judge:
            judge_decision = finding_decision(judge.evaluate(message, scenario))
            llm_decisions.append(judge_decision)
            output.update(
                {
                    "llm_judge_label": judge_decision["label"],
                    "llm_judge_severity": judge_decision["severity"],
                    "llm_judge_violation": judge_decision["violation"],
                    "llm_judge_findings_json": judge_decision["findings_json"],
                }
            )
        else:
            try:
                existing = parse_existing_findings(str(row.get("llm_judge_findings_json", "")))
            except (json.JSONDecodeError, ValueError):
                existing = []
            if existing:
                judge_decision = finding_decision(existing)
                llm_decisions.append(judge_decision)
                output.update(
                    {
                        "llm_judge_label": judge_decision["label"],
                        "llm_judge_severity": judge_decision["severity"],
                        "llm_judge_violation": judge_decision["violation"],
                        "llm_judge_findings_json": judge_decision["findings_json"],
                    }
                )
        adjudicated = adjudicated_decision(row)
        adjudicated_mask.append(adjudicated is not None)
        if adjudicated is not None:
            adjudicated_decisions.append(adjudicated)
            output.update(
                {
                    "adjudicated_label": adjudicated["label"],
                    "adjudicated_severity": adjudicated["severity"],
                    "adjudicated_violation": adjudicated["violation"],
                }
            )
        prediction_rows.append(output)

    rows = [summary_row("deterministic_summary", deterministic_decisions)]
    if len(llm_decisions) == len(deterministic_decisions):
        rows.append(comparison_row("deterministic_vs_llm_judge", deterministic_decisions, llm_decisions))
    if adjudicated_decisions:
        det_adjudicated = [decision for decision, keep in zip(deterministic_decisions, adjudicated_mask, strict=True) if keep]
        rows.append(comparison_row("deterministic_vs_adjudicated", det_adjudicated, adjudicated_decisions))
        if len(llm_decisions) == len(deterministic_decisions):
            llm_adjudicated = [decision for decision, keep in zip(llm_decisions, adjudicated_mask, strict=True) if keep]
            rows.append(comparison_row("llm_judge_vs_adjudicated", llm_adjudicated, adjudicated_decisions))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "comparison",
        "n_items",
        "left_violation_rate",
        "right_violation_rate",
        "label_agreement",
        "binary_violation_agreement",
        "label_kappa",
        "binary_violation_kappa",
        "precision_left_vs_right",
        "recall_left_vs_right",
        "f1_left_vs_right",
        "mean_max_severity",
    ]
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    write_predictions(Path(args.predictions_out), prediction_rows)
    print(f"Wrote {len(rows)} agreement rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
