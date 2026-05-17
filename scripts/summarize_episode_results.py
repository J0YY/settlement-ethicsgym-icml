from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_experiment import result_row
from segym.analysis.metrics import aggregate_by_model
from segym.logging import write_json
from segym.types import EpisodeResult, Scenario


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected YAML object in {path}")
    return data


def model_map(config_paths: list[Path]) -> dict[str, dict[str, Any]]:
    models: dict[str, dict[str, Any]] = {}
    for path in config_paths:
        config = load_config(path)
        for model in config.get("models", []):
            model_id = str(model.get("id", ""))
            if not model_id:
                raise ValueError(f"model without id in {path}")
            existing = models.get(model_id)
            if existing is not None and existing != model:
                raise ValueError(f"conflicting model config for {model_id}")
            models[model_id] = dict(model)
    return models


def infer_seed(run_dir: Path, default: int | None) -> int:
    if default is not None:
        return default
    match = re.search(r"_seed(\d+)$", run_dir.name)
    if match:
        return int(match.group(1))
    return 0


def episode_dirs(run_dir: Path) -> list[Path]:
    root = run_dir / "episodes"
    if not root.exists():
        raise FileNotFoundError(f"missing episodes directory: {root}")
    dirs = [path for path in root.iterdir() if path.is_dir() and (path / "result.json").exists()]
    return sorted(dirs, key=lambda path: path.name)


def redacted_model_configs(models: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    configs = []
    for model in models.values():
        redacted = dict(model)
        for key in list(redacted):
            if "api_key" in key.lower():
                redacted[key] = "[redacted]"
        configs.append(redacted)
    return configs


def write_metadata(run_dir: Path, rows: list[dict[str, Any]], models: dict[str, dict[str, Any]], seed: int) -> None:
    write_json(
        run_dir / "metadata.json",
        {
            "experiment_name": "reconstructed_episode_summary",
            "run_dir": str(run_dir),
            "created_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "seed": seed,
            "episode_rows": len(rows),
            "scenario_split": "",
            "models": sorted({str(row["model_id"]) for row in rows}),
            "model_configs": redacted_model_configs(models),
            "conditions": sorted({str(row["condition"]) for row in rows}),
            "fake_model_env": os.environ.get("SEGYN_FAKE_MODEL", ""),
            "reconstructed_from_episode_json": True,
        },
    )


def summarize_run(
    run_dir: Path,
    *,
    models: dict[str, dict[str, Any]],
    seed: int,
    output: Path,
    overwrite: bool,
    write_metadata_file: bool,
) -> int:
    if output.exists() and not overwrite:
        raise FileExistsError(f"{output} already exists; pass --overwrite to replace it")

    rows: list[dict[str, Any]] = []
    for episode_dir in episode_dirs(run_dir):
        result = EpisodeResult.model_validate(load_json(episode_dir / "result.json"))
        scenario = Scenario.model_validate(load_json(episode_dir / "scenario.json"))
        model = models.get(result.model_id)
        if model is None:
            raise KeyError(f"no model config supplied for {result.model_id}")
        rows.append(result_row(result, scenario, model, result.condition, seed))

    rows.sort(key=lambda row: (str(row["model_id"]), str(row["condition"]), str(row["scenario_id"])))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    if write_metadata_file:
        write_metadata(run_dir, rows, models, seed)

    aggregate = aggregate_by_model(pd.DataFrame(rows))
    records = aggregate.astype(object).where(pd.notna(aggregate), None).to_dict(orient="records")
    write_json(run_dir / "aggregate_metrics.json", records)
    print(f"wrote {len(rows)} rows to {output}")
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--config", action="append", required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-metadata", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    output = Path(args.output) if args.output else run_dir / "summary.csv"
    seed = infer_seed(run_dir, args.seed)
    summarize_run(
        run_dir,
        models=model_map([Path(path) for path in args.config]),
        seed=seed,
        output=output,
        overwrite=args.overwrite,
        write_metadata_file=not args.no_metadata,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
