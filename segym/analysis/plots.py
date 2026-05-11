from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_violation_rates(summary: pd.DataFrame, out_path: str | Path) -> None:
    if summary.empty:
        return
    fig, ax = plt.subplots(figsize=(7, 4))
    labels = summary["model_id"].astype(str)
    ax.bar(labels, summary["material_misrepresentation_rate"], color="#356f8c")
    ax.set_ylabel("Material misrepresentation rate")
    ax.set_xlabel("Condition / model")
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_pareto(summary: pd.DataFrame, out_path: str | Path) -> None:
    if summary.empty:
        return
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(summary["material_misrepresentation_rate"], summary["mean_client_utility"], color="#7a4e9f")
    for _, row in summary.iterrows():
        ax.annotate(str(row["model_id"]), (row["material_misrepresentation_rate"], row["mean_client_utility"]), fontsize=7)
    ax.set_xlabel("Violation rate")
    ax.set_ylabel("Mean client utility")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    fig.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)

