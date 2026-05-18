from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


DEFAULT_MULTIPLIERS = [0.75, 0.9, 1.0, 1.15, 1.3, 1.5]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=False)


def scaled_amount(value: Any, multiplier: float) -> Any:
    if not isinstance(value, int):
        return value
    return max(1000, int(round((value * multiplier) / 1000.0) * 1000))


def scale_money_fields(data: dict[str, Any], multiplier: float) -> None:
    initial_offer = data.get("initial_offer")
    if isinstance(initial_offer, dict) and "amount_usd" in initial_offer:
        initial_offer["amount_usd"] = scaled_amount(initial_offer["amount_usd"], multiplier)
    reservation_values = data.get("reservation_values")
    if isinstance(reservation_values, dict):
        for key, value in list(reservation_values.items()):
            if key.endswith("_usd"):
                reservation_values[key] = scaled_amount(value, multiplier)


def variant_for(base: dict[str, Any], index: int, multiplier: float) -> dict[str, Any]:
    data = deepcopy(base)
    original_id = str(base["scenario_id"])
    data["scenario_id"] = f"{original_id}_blindspot_v{index:02d}"
    data["title"] = f"{base.get('title', original_id)} - blindspot variant {index:02d}"
    data["created_by"] = "generated_blindspot_variant"
    data["review_status"] = "unreviewed"
    data["source_type"] = "synthetic"
    scale_money_fields(data, multiplier)
    summary = str(data.get("public_case_summary", "")).strip()
    data["public_case_summary"] = (
        f"{summary} Variant {index:02d} rescales settlement economics by {multiplier:.2f}x "
        "while preserving the same hidden-fact blindspot."
    )
    return data


def generate(source_dir: Path, out_dir: Path, split_out: Path, multipliers: list[float]) -> list[Path]:
    source_paths = sorted(path for path in source_dir.glob("*.yaml") if path.is_file())
    written: list[Path] = []
    for source_path in source_paths:
        base = load_yaml(source_path)
        for index, multiplier in enumerate(multipliers, start=1):
            data = variant_for(base, index, multiplier)
            out_path = out_dir / f"{data['scenario_id']}.yaml"
            write_yaml(out_path, data)
            written.append(out_path)
    split_out.parent.mkdir(parents=True, exist_ok=True)
    split_out.write_text("\n".join(str(path) for path in written) + "\n", encoding="utf-8")
    return written


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default="data/scenarios/blindspot")
    parser.add_argument("--out-dir", default="data/scenarios/blindspot/v0.2")
    parser.add_argument("--split-out", default="data/splits/blindspot_stress_v0_2_24.txt")
    parser.add_argument("--multiplier", type=float, action="append", dest="multipliers")
    args = parser.parse_args()

    written = generate(
        Path(args.source_dir),
        Path(args.out_dir),
        Path(args.split_out),
        args.multipliers or DEFAULT_MULTIPLIERS,
    )
    print(f"Wrote {len(written)} blindspot scenario variants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
