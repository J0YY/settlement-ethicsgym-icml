from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from segym.analysis.metrics import aggregate_by_model, load_summary
from segym.analysis.plots import plot_pareto, plot_violation_rates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", action="append", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--figures", default="paper/figures")
    parser.add_argument(
        "--latest-only",
        action="store_true",
        help="Use only the most recent timestamped run under each --run-dir.",
    )
    parser.add_argument(
        "--require-real",
        action="store_true",
        help="Fail if any selected run is missing metadata or is marked as fake.",
    )
    args = parser.parse_args()

    df = load_summary(args.run_dir, latest_only=args.latest_only, require_real=args.require_real)
    summary = aggregate_by_model(df)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out, index=False)
    plot_violation_rates(summary, Path(args.figures) / "violation_rates.png")
    plot_pareto(summary, Path(args.figures) / "pareto.png")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
