from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import pandas as pd


PathInput = str | Path


def _as_paths(paths: PathInput | Sequence[PathInput]) -> list[Path]:
    if isinstance(paths, str | Path):
        return [Path(paths)]
    return [Path(path) for path in paths]


def discover_summary_paths(run_dirs: PathInput | Sequence[PathInput], *, latest_only: bool = False) -> list[Path]:
    summary_paths: list[Path] = []
    for run_dir in _as_paths(run_dirs):
        if run_dir.name == "summary.csv" and run_dir.is_file():
            candidates = [run_dir]
        elif (run_dir / "summary.csv").exists():
            candidates = [run_dir / "summary.csv"]
        else:
            candidates = sorted(run_dir.glob("*/summary.csv"))
        if latest_only and candidates:
            candidates = [max(candidates, key=lambda path: path.parent.name)]
        summary_paths.extend(candidates)
    return sorted(dict.fromkeys(summary_paths))


def _load_metadata(summary_path: Path) -> dict:
    metadata_path = summary_path.parent / "metadata.json"
    if not metadata_path.exists():
        return {}
    with metadata_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _looks_true(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def validate_non_fake_run(summary_path: Path, frame: pd.DataFrame, metadata: dict) -> None:
    reasons: list[str] = []
    if not metadata:
        reasons.append("missing metadata.json")
    if _looks_true(metadata.get("fake_model_env")):
        reasons.append('metadata fake_model_env is truthy')
    for model in metadata.get("model_configs", []):
        if _looks_true(model.get("fake")):
            reasons.append(f"model config {model.get('id', '<unknown>')} has fake=true")
        if str(model.get("provider", "")).strip().lower() == "fake":
            reasons.append(f"model config {model.get('id', '<unknown>')} uses provider=fake")
    if "provider" in frame.columns:
        providers = {str(provider).strip().lower() for provider in frame["provider"].dropna() if str(provider).strip()}
        if "fake" in providers:
            reasons.append("summary.csv contains provider=fake")
    if reasons:
        reason_text = "; ".join(reasons)
        raise ValueError(f"{summary_path.parent} is not an eligible real run: {reason_text}")


def load_summary(
    run_dir: PathInput | Sequence[PathInput],
    *,
    latest_only: bool = False,
    require_real: bool = False,
    add_provenance: bool = True,
) -> pd.DataFrame:
    paths = discover_summary_paths(run_dir, latest_only=latest_only)
    frames = []
    for path in paths:
        frame = pd.read_csv(path)
        metadata = _load_metadata(path)
        if require_real:
            validate_non_fake_run(path, frame, metadata)
        if add_provenance:
            frame = frame.copy()
            frame["source_run_dir"] = str(path.parent)
            frame["source_summary_path"] = str(path)
            frame["source_experiment_name"] = metadata.get("experiment_name", path.parent.parent.name)
            frame["source_fake_model_env"] = metadata.get("fake_model_env", "")
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def aggregate_by_model(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    grouped = df.groupby(["model_id", "condition"], dropna=False)
    summary = grouped.agg(
        episodes=("scenario_id", "count"),
        settlement_rate=("settled", "mean"),
        mean_client_utility=("client_utility", "mean"),
        material_misrepresentation_rate=("episode_has_material_violation", "mean"),
        severe_violation_rate=("episode_has_severe_violation", "mean"),
        mean_violation_count=("material_violation_count", "mean"),
    ).reset_index()
    for column, output_column in [
        ("safe_candidate_available", "safe_candidate_available_rate"),
        ("selected_unsafe_despite_safe", "selected_unsafe_despite_safe_rate"),
        ("shield_triggered", "shield_triggered_rate"),
        ("llm_parse_failed", "llm_parse_failed_rate"),
    ]:
        if column not in df.columns:
            continue
        enriched = df.copy()
        enriched[column] = enriched[column].map(
            {
                True: 1.0,
                False: 0.0,
                "True": 1.0,
                "False": 0.0,
            }
        )
        optional = (
            enriched.dropna(subset=[column])
            .groupby(["model_id", "condition"], dropna=False)[column]
            .mean()
            .reset_index(name=output_column)
        )
        summary = summary.merge(optional, on=["model_id", "condition"], how="left")
    if "shield_trigger_count" in df.columns:
        enriched = df.copy()
        enriched["shield_trigger_count"] = pd.to_numeric(enriched["shield_trigger_count"], errors="coerce")
        optional = (
            enriched.dropna(subset=["shield_trigger_count"])
            .groupby(["model_id", "condition"], dropna=False)["shield_trigger_count"]
            .mean()
            .reset_index(name="mean_shield_trigger_count")
        )
        summary = summary.merge(optional, on=["model_id", "condition"], how="left")
    if "llm_parse_failure_count" in df.columns:
        enriched = df.copy()
        enriched["llm_parse_failure_count"] = pd.to_numeric(enriched["llm_parse_failure_count"], errors="coerce")
        optional = (
            enriched.dropna(subset=["llm_parse_failure_count"])
            .groupby(["model_id", "condition"], dropna=False)["llm_parse_failure_count"]
            .mean()
            .reset_index(name="mean_llm_parse_failure_count")
        )
        summary = summary.merge(optional, on=["model_id", "condition"], how="left")
    return summary
