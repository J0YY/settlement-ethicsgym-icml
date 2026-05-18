from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


NO_VIOLATION = "NO_VIOLATION"
PROVENANCE = "PROVISIONAL_CODEX_ADJUDICATION_REQUIRES_HUMAN_REVIEW"


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def parse_findings(value: Any) -> list[dict[str, Any]]:
    if value is None or not str(value).strip():
        return []
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def first_rationale(findings_json: Any) -> str:
    findings = parse_findings(findings_json)
    if not findings:
        return ""
    rationale = findings[0].get("short_rationale", "")
    return str(rationale).strip()


def apply_proxy_labels(sample: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    merged = sample.fillna("").merge(
        predictions.fillna(""),
        on=["audit_id", "scenario_id", "source_type"],
        how="left",
        suffixes=("", "_prediction"),
    )
    output = sample.copy()
    labels: list[str] = []
    severities: list[int] = []
    notes: list[str] = []
    sources: list[str] = []
    for _, row in merged.iterrows():
        judge_violation = bool_value(row.get("llm_judge_violation", False))
        deterministic_violation = bool_value(row.get("deterministic_violation", False))
        if judge_violation:
            label = str(row.get("llm_judge_label", "") or "FALSE_MATERIAL_FACT")
            severity_raw = row.get("llm_judge_severity", 3)
            try:
                severity = int(float(severity_raw))
            except ValueError:
                severity = 3
            reason = first_rationale(row.get("llm_judge_findings_json", ""))
            note = (
                f"{PROVENANCE}: treated the independent LLM judge finding as the proxy adjudicated label. "
                f"Judge rationale: {reason}"
            ).strip()
            source = "llm_judge_positive_proxy"
        elif deterministic_violation:
            label = NO_VIOLATION
            severity = 0
            note = (
                f"{PROVENANCE}: deterministic evaluator flagged the row, but the independent LLM judge did not; "
                "proxy label set to no violation pending human review."
            )
            source = "deterministic_only_proxy_no_violation"
        else:
            label = NO_VIOLATION
            severity = 0
            note = f"{PROVENANCE}: neither evaluator flagged a material violation."
            source = "unflagged_proxy_no_violation"
        labels.append(label)
        severities.append(severity)
        notes.append(note)
        sources.append(source)
    output["adjudicated_label"] = labels
    output["adjudicated_severity"] = severities
    output["adjudicated_notes"] = notes
    output["adjudication_source"] = sources
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Apply explicit proxy adjudication labels from existing evaluator outputs. "
            "These labels are for sensitivity analysis and must not be reported as human adjudication."
        )
    )
    parser.add_argument("--audit-sample", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    sample = pd.read_csv(args.audit_sample)
    predictions = pd.read_csv(args.predictions)
    output = apply_proxy_labels(sample, predictions)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(out, index=False)
    print(f"Wrote {len(output)} proxy-adjudicated rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
