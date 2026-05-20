from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.add_wilson_intervals import wilson_interval


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def fmt(value: float | None) -> str:
    return "" if value is None or pd.isna(value) else f"{value:.6f}"


def wilson_fields(successes: int, denominator: int) -> dict[str, str]:
    low, high = wilson_interval(successes, denominator) if denominator else (None, None)
    return {
        "count": str(successes),
        "denominator": str(denominator),
        "rate": fmt(successes / denominator if denominator else None),
        "wilson95_low": fmt(low),
        "wilson95_high": fmt(high),
    }


def parse_prediction_arg(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("Prediction inputs must be NAME=PATH")
    name, path = raw.split("=", 1)
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError("Prediction NAME cannot be empty")
    return name, Path(path)


def load_judge_predictions(inputs: list[tuple[str, Path]]) -> dict[str, pd.DataFrame]:
    predictions = {}
    for name, path in inputs:
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path).fillna("")
        required = {"audit_id", "llm_judge_violation"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
        predictions[name] = frame
    return predictions


def aggregate(sample_path: Path, prediction_inputs: list[tuple[str, Path]]) -> pd.DataFrame:
    sample = pd.read_csv(sample_path).fillna("")
    if "audit_id" not in sample.columns:
        raise ValueError(f"{sample_path} is missing audit_id")
    merged = sample.copy()
    judge_names = []
    for name, frame in load_judge_predictions(prediction_inputs).items():
        judge_names.append(name)
        columns = ["audit_id", "llm_judge_violation", "llm_judge_label", "llm_judge_severity"]
        frame = frame[[column for column in columns if column in frame.columns]].copy()
        frame = frame.rename(
            columns={
                "llm_judge_violation": f"{name}_violation",
                "llm_judge_label": f"{name}_label",
                "llm_judge_severity": f"{name}_severity",
            }
        )
        merged = merged.merge(frame, on="audit_id", how="left")

    violation_columns = [f"{name}_violation" for name in judge_names]
    if not violation_columns:
        raise ValueError("At least one judge prediction file is required")

    judge_votes = merged[violation_columns].map(bool_value)
    available = merged[violation_columns].notna() & (merged[violation_columns].astype(str).apply(lambda col: col.str.len()) > 0)
    merged["judge_count"] = available.sum(axis=1)
    merged["judge_positive_count"] = judge_votes.sum(axis=1)
    merged["any_judge_violation"] = merged["judge_positive_count"] > 0
    merged["majority_judge_violation"] = merged["judge_positive_count"] > (merged["judge_count"] / 2)
    merged["unanimous_judge_violation"] = (
        (merged["judge_count"] > 0) & (merged["judge_positive_count"] == merged["judge_count"])
    )
    merged["judge_disagreement"] = (
        (merged["judge_count"] > 1)
        & (merged["judge_positive_count"] > 0)
        & (merged["judge_positive_count"] < merged["judge_count"])
    )
    return merged


def summary_rows(frame: pd.DataFrame, group_columns: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    groups = [((), frame)] if not group_columns else frame.groupby(group_columns, dropna=False)
    for key, group in groups:
        key_values = key if isinstance(key, tuple) else (key,)
        base = {column: str(value) for column, value in zip(group_columns, key_values, strict=True)}
        denominator = len(group)
        for metric in [
            "any_judge_violation",
            "majority_judge_violation",
            "unanimous_judge_violation",
            "judge_disagreement",
        ]:
            count = sum(bool_value(value) for value in group[metric])
            row = {
                **base,
                "metric": metric,
                "mean_judge_count": fmt(group["judge_count"].mean()),
                "mean_positive_judge_count": fmt(group["judge_positive_count"].mean()),
            }
            row.update(wilson_fields(count, denominator))
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({field for row in rows for field in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate multiple independent LLM-judge prediction CSVs into any/majority/unanimous "
            "sensitivity rates. These are automated robustness checks, not human adjudication."
        )
    )
    parser.add_argument("--audit-sample", required=True)
    parser.add_argument("--prediction", action="append", type=parse_prediction_arg, required=True)
    parser.add_argument("--out-rows", required=True)
    parser.add_argument("--out-summary", required=True)
    parser.add_argument("--group-by", action="append", default=[])
    args = parser.parse_args()

    aggregated = aggregate(Path(args.audit_sample), args.prediction)
    Path(args.out_rows).parent.mkdir(parents=True, exist_ok=True)
    aggregated.to_csv(args.out_rows, index=False)
    write_csv(Path(args.out_summary), summary_rows(aggregated, args.group_by))
    print(f"Wrote {len(aggregated)} aggregate rows to {args.out_rows}")
    print(f"Wrote multi-judge summary to {args.out_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
