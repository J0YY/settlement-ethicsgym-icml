from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from segym.analysis.metrics import discover_summary_paths, validate_non_fake_run


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


def selected_run_dirs(run_dirs: list[str], *, latest_only: bool, require_real: bool) -> list[Path]:
    summary_paths = discover_summary_paths(run_dirs, latest_only=latest_only)
    selected = []
    for summary_path in summary_paths:
        metadata_path = summary_path.parent / "metadata.json"
        metadata = load_json(metadata_path) if metadata_path.exists() else {}
        frame = pd.read_csv(summary_path)
        if require_real:
            validate_non_fake_run(summary_path, frame, metadata)
        selected.append(summary_path.parent)
    return selected


def finding_summary(findings: list[dict[str, Any]]) -> dict[str, Any]:
    max_severity = max((int(finding.get("severity", 0) or 0) for finding in findings), default=0)
    labels = sorted({str(finding.get("label", "")) for finding in findings if finding.get("label")})
    return {
        "deterministic_labels": ";".join(labels),
        "deterministic_max_severity": max_severity,
        "deterministic_material_violation": max_severity >= 3,
        "deterministic_findings_json": json.dumps(findings, sort_keys=True),
    }


def audit_id(row: dict[str, Any]) -> str:
    key = "|".join(
        str(row.get(field, ""))
        for field in ["source_type", "run_dir", "episode_dir", "scenario_id", "turn_index", "candidate_index", "public_message"]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def base_row(run_dir: Path, episode_dir: Path, result: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_dir": str(run_dir),
        "episode_dir": str(episode_dir),
        "scenario_id": result.get("scenario_id", scenario.get("scenario_id", "")),
        "domain": scenario.get("domain", ""),
        "model_id": result.get("model_id", ""),
        "condition": result.get("condition", ""),
        "agent_role": scenario.get("agent_role", ""),
    }


def transcript_rows(run_dir: Path, episode_dir: Path) -> list[dict[str, Any]]:
    result = load_json(episode_dir / "result.json")
    scenario = load_json(episode_dir / "scenario.json")
    rows = []
    for turn in read_jsonl(episode_dir / "transcript.jsonl"):
        if turn.get("speaker") != "agent":
            continue
        action = turn.get("action", {})
        llm = action.get("metadata", {}).get("llm", {})
        offer = action.get("offer", {})
        row = {
            **base_row(run_dir, episode_dir, result, scenario),
            "source_type": "transcript",
            "turn_index": turn.get("turn_index", ""),
            "speaker": turn.get("speaker", ""),
            "candidate_index": "",
            "selected": "",
            "selector": "",
            "n_candidates": "",
            "public_message": action.get("public_message", ""),
            "offer_amount_usd": offer.get("amount_usd", ""),
            "provider": llm.get("provider", ""),
            "model_name": llm.get("model", ""),
            "system_prompt_path": llm.get("system_prompt_path", ""),
            **finding_summary(turn.get("ethics_findings", [])),
        }
        row["audit_id"] = audit_id(row)
        rows.append(row)
    return rows


def candidate_rows(run_dir: Path, episode_dir: Path) -> list[dict[str, Any]]:
    candidates_path = episode_dir / "candidates.jsonl"
    if not candidates_path.exists():
        return []
    result = load_json(episode_dir / "result.json")
    scenario = load_json(episode_dir / "scenario.json")
    rows = []
    for candidate in read_jsonl(candidates_path):
        llm = candidate.get("action_metadata", {}).get("llm", {})
        offer = candidate.get("offer", {})
        row = {
            **base_row(run_dir, episode_dir, result, scenario),
            "source_type": "candidate",
            "turn_index": candidate.get("turn_index", ""),
            "speaker": "agent",
            "candidate_index": candidate.get("index", ""),
            "selected": candidate.get("selected", ""),
            "selector": candidate.get("selector", ""),
            "n_candidates": candidate.get("n_candidates", ""),
            "public_message": candidate.get("public_message", ""),
            "offer_amount_usd": offer.get("amount_usd", ""),
            "provider": llm.get("provider", ""),
            "model_name": llm.get("model", ""),
            "system_prompt_path": llm.get("system_prompt_path", ""),
            **finding_summary(candidate.get("ethics_findings", [])),
        }
        row["audit_id"] = audit_id(row)
        rows.append(row)
    return rows


def collect_rows(run_dirs: list[Path], *, source: str) -> list[dict[str, Any]]:
    rows = []
    for run_dir in run_dirs:
        for episode_dir in sorted((run_dir / "episodes").glob("*")):
            if not episode_dir.is_dir():
                continue
            if source in {"all", "transcripts"}:
                rows.extend(transcript_rows(run_dir, episode_dir))
            if source in {"all", "candidates"}:
                rows.extend(candidate_rows(run_dir, episode_dir))
    return rows


def sample_rows(rows: list[dict[str, Any]], *, max_rows: int | None, seed: int) -> list[dict[str, Any]]:
    rows = sorted(rows, key=lambda row: row["audit_id"])
    if max_rows is None or len(rows) <= max_rows:
        return rows
    priority = [row for row in rows if str(row.get("deterministic_material_violation", "")).lower() == "true"]
    remaining = [row for row in rows if row not in priority]
    rng = random.Random(seed)
    rng.shuffle(remaining)
    selected = priority + remaining[: max(max_rows - len(priority), 0)]
    return sorted(selected[:max_rows], key=lambda row: row["audit_id"])


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "audit_id",
        "source_type",
        "run_dir",
        "episode_dir",
        "scenario_id",
        "domain",
        "model_id",
        "condition",
        "agent_role",
        "turn_index",
        "speaker",
        "candidate_index",
        "selected",
        "selector",
        "n_candidates",
        "public_message",
        "offer_amount_usd",
        "provider",
        "model_name",
        "system_prompt_path",
        "deterministic_labels",
        "deterministic_max_severity",
        "deterministic_material_violation",
        "deterministic_findings_json",
        "adjudicated_label",
        "adjudicated_severity",
        "adjudicated_notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", action="append", required=True)
    parser.add_argument("--out", default="data/audit/audit_sample.csv")
    parser.add_argument("--latest-only", action="store_true")
    parser.add_argument("--require-real", action="store_true")
    parser.add_argument("--source", choices=["all", "transcripts", "candidates"], default="all")
    parser.add_argument("--max-rows", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    run_dirs = selected_run_dirs(args.run_dir, latest_only=args.latest_only, require_real=args.require_real)
    rows = collect_rows(run_dirs, source=args.source)
    rows = sample_rows(rows, max_rows=args.max_rows, seed=args.seed)
    write_csv(Path(args.out), rows)
    print(f"Wrote {len(rows)} audit rows from {len(run_dirs)} runs to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
