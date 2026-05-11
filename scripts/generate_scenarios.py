from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=False)


def scale_money(data: dict, multiplier: float) -> None:
    for key, value in list(data.get("reservation_values", {}).items()):
        if isinstance(value, int):
            data["reservation_values"][key] = max(1000, int(round(value * multiplier / 1000) * 1000))
    if data.get("initial_offer"):
        data["initial_offer"]["amount_usd"] = max(
            1000, int(round(data["initial_offer"]["amount_usd"] * multiplier / 1000) * 1000)
        )


def variant(seed: dict, index: int, multiplier: float) -> dict:
    data = copy.deepcopy(seed)
    base_id = seed["scenario_id"]
    data["scenario_id"] = f"{base_id}_var{index:02d}"
    data["title"] = f"{seed['title']} (variant {index})"
    data["created_by"] = "template_generated"
    data["review_status"] = "unreviewed"
    scale_money(data, multiplier)
    data["public_case_summary"] += f" This generated variant uses amount multiplier {multiplier:.2f}."
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-dir", default="data/scenarios/seed")
    parser.add_argument("--out-dir", default="data/scenarios/generated/v0.1")
    parser.add_argument("--split-out", default="data/splits/generated_v0_1.txt")
    parser.add_argument("--variants-per-seed", type=int, default=3)
    args = parser.parse_args()

    seed_paths = sorted(Path(args.seed_dir).glob("*.yaml"))
    multipliers = [0.85, 1.00, 1.15, 1.30]
    generated_paths: list[Path] = []
    for seed_path in seed_paths:
        seed = load_yaml(seed_path)
        for idx in range(1, args.variants_per_seed + 1):
            data = variant(seed, idx, multipliers[(idx - 1) % len(multipliers)])
            out_path = Path(args.out_dir) / f"{data['scenario_id']}.yaml"
            write_yaml(out_path, data)
            generated_paths.append(out_path)

    split_path = Path(args.split_out)
    split_path.parent.mkdir(parents=True, exist_ok=True)
    split_path.write_text("\n".join(str(path) for path in generated_paths) + "\n", encoding="utf-8")
    print(f"Generated {len(generated_paths)} scenarios into {args.out_dir}")
    print(f"Wrote split {split_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

