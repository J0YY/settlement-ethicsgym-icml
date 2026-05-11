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
    return grouped.agg(
        episodes=("scenario_id", "count"),
        settlement_rate=("settled", "mean"),
        mean_client_utility=("client_utility", "mean"),
        material_misrepresentation_rate=("episode_has_material_violation", "mean"),
        severe_violation_rate=("episode_has_severe_violation", "mean"),
        mean_violation_count=("material_violation_count", "mean"),
    ).reset_index()

