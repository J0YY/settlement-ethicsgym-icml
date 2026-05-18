from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd


RATE_COLUMNS = [
    "settlement_rate",
    "material_misrepresentation_rate",
    "severe_violation_rate",
    "safe_candidate_available_rate",
    "selected_unsafe_despite_safe_rate",
    "shield_triggered_rate",
    "llm_parse_failed_rate",
]


def wilson_interval(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n <= 0:
        return (math.nan, math.nan)
    phat = successes / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    half_width = z * math.sqrt((phat * (1 - phat) + z**2 / (4 * n)) / n) / denom
    low = max(0.0, center - half_width)
    high = min(1.0, center + half_width)
    if successes == 0:
        low = 0.0
    if successes == n:
        high = 1.0
    return low, high


def add_intervals(frame: pd.DataFrame, *, rate_columns: list[str]) -> pd.DataFrame:
    output = frame.copy()
    if "episodes" not in output.columns:
        raise ValueError("input summary must include an episodes column")
    for column in rate_columns:
        if column not in output.columns:
            continue
        lows = []
        highs = []
        counts = []
        for _, row in output.iterrows():
            rate = row.get(column)
            n = int(row["episodes"])
            if pd.isna(rate):
                lows.append(math.nan)
                highs.append(math.nan)
                counts.append(math.nan)
                continue
            successes = int(round(float(rate) * n))
            low, high = wilson_interval(successes, n)
            lows.append(low)
            highs.append(high)
            counts.append(successes)
        output[f"{column}_count"] = counts
        output[f"{column}_wilson95_low"] = lows
        output[f"{column}_wilson95_high"] = highs
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--rate-column", action="append", dest="rate_columns")
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    enriched = add_intervals(frame, rate_columns=args.rate_columns or RATE_COLUMNS)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(out, index=False)
    print(f"Wrote Wilson intervals for {len(enriched)} rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
