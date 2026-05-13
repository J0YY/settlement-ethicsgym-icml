from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_summary(run_dir: str | Path) -> pd.DataFrame:
    paths = sorted(Path(run_dir).glob("*/summary.csv"))
    if not paths and (Path(run_dir) / "summary.csv").exists():
        paths = [Path(run_dir) / "summary.csv"]
    frames = [pd.read_csv(path) for path in paths]
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
