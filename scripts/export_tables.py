from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from segym.analysis.metrics import aggregate_by_model, load_summary


def to_simple_latex(summary) -> str:
    columns = [
        "model_id",
        "episodes",
        "settlement_rate",
        "mean_client_utility",
        "material_misrepresentation_rate",
        "severe_violation_rate",
    ]
    header = [
        "Model",
        "Episodes",
        "Settle",
        "Utility",
        "Misrep.",
        "Severe",
    ]
    lines = [
        "\\begin{tabular}{lrrrrr}",
        "\\toprule",
        " & ".join(header) + " \\\\",
        "\\midrule",
    ]
    for _, row in summary.iterrows():
        cells = []
        for col in columns:
            value = row[col]
            if col == "model_id":
                cells.append(str(value).replace("_", "\\_"))
            elif col == "episodes":
                cells.append(str(int(value)))
            else:
                cells.append(f"{float(value):.3f}")
        lines.append(" & ".join(cells) + " \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--format", choices=["latex", "csv"], default="latex")
    parser.add_argument("--out", default="paper/tables")
    args = parser.parse_args()
    summary = aggregate_by_model(load_summary(args.run_dir))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.format == "csv":
        summary.to_csv(out_dir / "main_results.csv", index=False)
    else:
        (out_dir / "main_results.tex").write_text(to_simple_latex(summary), encoding="utf-8")
    print(f"Wrote tables to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
