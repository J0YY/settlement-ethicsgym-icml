from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.make_audit_sample import collect_rows, selected_run_dirs


def contains_any(value: str, needles: list[str]) -> bool:
    return any(needle in value for needle in needles)


STRATA: dict[str, Callable[[dict[str, object]], bool]] = {
    "shield_rewrite": lambda row: contains_any(
        str(row.get("model_id", "")),
        ["shield_rewrite", "shield_rewrite_ablation"],
    ),
    "shield_warn_only": lambda row: "shield_warn_only" in str(row.get("model_id", "")),
    "base_stress": lambda row: contains_any(
        str(row.get("model_id", "")),
        ["llm_stress_utility_prompt", "gpt41_nano_stress_utility_prompt"],
    ),
    "bon_utility": lambda row: (
        "best_of_n_utility" in str(row.get("model_id", ""))
        or "stress_best_of_n_utility" in str(row.get("model_id", ""))
    ),
    "bon_ethics": lambda row: (
        "best_of_n_ethics" in str(row.get("model_id", ""))
        or "stress_best_of_n_ethics" in str(row.get("model_id", ""))
    ),
}


def priority_key(row: dict[str, object]) -> tuple[int, str, str]:
    material = str(row.get("deterministic_material_violation", "")).lower() == "true"
    selected = str(row.get("selected", "")).lower() == "true"
    transcript = row.get("source_type") == "transcript"
    return (
        0 if material else 1,
        "0" if selected or transcript else "1",
        str(row.get("audit_id", "")),
    )


def sample_strata(
    rows: list[dict[str, object]],
    *,
    per_stratum: int,
    seed: int,
    include_unmatched: bool,
) -> list[dict[str, object]]:
    rng = random.Random(seed)
    selected: list[dict[str, object]] = []
    used: set[str] = set()
    for stratum, predicate in STRATA.items():
        candidates = [dict(row, audit_stratum=stratum) for row in rows if predicate(row)]
        priority = sorted(candidates, key=priority_key)
        if len(priority) > per_stratum:
            material = [row for row in priority if str(row.get("deterministic_material_violation", "")).lower() == "true"]
            rest = [row for row in priority if row not in material]
            rng.shuffle(rest)
            priority = sorted((material + rest)[:per_stratum], key=priority_key)
        for row in priority:
            audit_id = str(row.get("audit_id", ""))
            if audit_id and audit_id not in used:
                used.add(audit_id)
                selected.append(row)
    if include_unmatched:
        for row in rows:
            audit_id = str(row.get("audit_id", ""))
            if audit_id and audit_id not in used:
                used.add(audit_id)
                selected.append(dict(row, audit_stratum="unmatched"))
    return sorted(selected, key=lambda row: (str(row.get("audit_stratum", "")), str(row.get("audit_id", ""))))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "audit_id",
        "audit_stratum",
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
    parser.add_argument("--out", default="data/audit/stratified_audit_sample.csv")
    parser.add_argument("--latest-only", action="store_true")
    parser.add_argument("--require-real", action="store_true")
    parser.add_argument("--source", choices=["all", "transcripts", "candidates"], default="all")
    parser.add_argument("--per-stratum", type=int, default=60)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--include-unmatched", action="store_true")
    args = parser.parse_args()

    run_dirs = selected_run_dirs(args.run_dir, latest_only=args.latest_only, require_real=args.require_real)
    rows = collect_rows(run_dirs, source=args.source)
    sampled = sample_strata(rows, per_stratum=args.per_stratum, seed=args.seed, include_unmatched=args.include_unmatched)
    write_csv(Path(args.out), sampled)
    counts: dict[str, int] = {}
    for row in sampled:
        counts[str(row.get("audit_stratum", ""))] = counts.get(str(row.get("audit_stratum", "")), 0) + 1
    print(f"Wrote {len(sampled)} stratified audit rows from {len(run_dirs)} runs to {args.out}")
    for stratum, count in sorted(counts.items()):
        print(f"{stratum}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
