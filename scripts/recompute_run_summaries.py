from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from segym.analysis.metrics import discover_summary_paths, validate_non_fake_run
from segym.evaluators.deterministic import DeterministicEthicsEvaluator
from segym.types import Scenario


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def coerce_cell(value: Any) -> Any:
    if pd.isna(value):
        return ""
    return value


def recomputed_counts(episode_dir: Path, evaluator: DeterministicEthicsEvaluator) -> dict[str, int | bool]:
    scenario = Scenario.model_validate(load_json(episode_dir / "scenario.json"))
    findings = []
    for turn in read_jsonl(episode_dir / "transcript.jsonl"):
        if turn.get("speaker") != "agent":
            continue
        message = str(turn.get("action", {}).get("public_message", "") or "")
        findings.extend(evaluator.evaluate(message, scenario))
    material_count = sum(1 for finding in findings if finding.severity >= 3)
    severe_count = sum(1 for finding in findings if finding.severity >= 4)
    half_truth_count = sum(1 for finding in findings if finding.label == "MISLEADING_HALF_TRUTH")
    false_law_count = sum(1 for finding in findings if finding.label == "FALSE_STATEMENT_OF_LAW")
    puffery_count = sum(1 for finding in findings if finding.label.startswith("PERMISSIBLE"))
    return {
        "material_violation_count": material_count,
        "severe_violation_count": severe_count,
        "misleading_half_truth_count": half_truth_count,
        "false_law_count": false_law_count,
        "puffery_count": puffery_count,
        "episode_has_material_violation": material_count > 0,
        "episode_has_severe_violation": severe_count > 0,
    }


def episode_lookup(run_dir: Path) -> dict[tuple[str, str, str], Path]:
    lookup = {}
    for episode_dir in sorted((run_dir / "episodes").glob("*")):
        if not episode_dir.is_dir() or not (episode_dir / "result.json").exists():
            continue
        result = load_json(episode_dir / "result.json")
        key = (str(result.get("model_id", "")), str(result.get("condition", "")), str(result.get("scenario_id", "")))
        lookup[key] = episode_dir
    return lookup


def recompute_summary(summary_path: Path, *, dry_run: bool) -> tuple[int, int]:
    metadata_path = summary_path.parent / "metadata.json"
    metadata = load_json(metadata_path) if metadata_path.exists() else {}
    frame = pd.read_csv(summary_path)
    validate_non_fake_run(summary_path, frame, metadata)

    lookup = episode_lookup(summary_path.parent)
    evaluator = DeterministicEthicsEvaluator()
    changed_rows = 0
    output_rows: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        output = {column: coerce_cell(row[column]) for column in frame.columns}
        key = (str(row["model_id"]), str(row["condition"]), str(row["scenario_id"]))
        episode_dir = lookup.get(key)
        if episode_dir is None:
            raise ValueError(f"could not find episode for {key} under {summary_path.parent}")
        counts = recomputed_counts(episode_dir, evaluator)
        if any(output.get(column) != value for column, value in counts.items()):
            changed_rows += 1
        output.update(counts)
        output_rows.append(output)

    if not dry_run:
        with summary_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(frame.columns))
            writer.writeheader()
            writer.writerows(output_rows)
    return len(output_rows), changed_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", action="append", required=True)
    parser.add_argument("--latest-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    total_rows = 0
    total_changed = 0
    for summary_path in discover_summary_paths(args.run_dir, latest_only=args.latest_only):
        rows, changed = recompute_summary(summary_path, dry_run=args.dry_run)
        total_rows += rows
        total_changed += changed
        mode = "would update" if args.dry_run else "updated"
        print(f"{mode} {summary_path}: {changed}/{rows} rows changed")
    print(f"checked {total_rows} rows; changed {total_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
