from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml

from segym.types import Scenario


def load_scenario(path: str | Path) -> Scenario:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return Scenario.model_validate(data)


def load_scenarios(paths: Iterable[str | Path]) -> list[Scenario]:
    return [load_scenario(path) for path in paths]


def find_scenario_path(scenario_id: str, roots: Iterable[str | Path] | None = None) -> Path:
    search_roots = (
        [Path("data/scenarios/seed"), Path("data/scenarios/generated/v0.1")]
        if roots is None
        else [Path(root) for root in roots]
    )
    for root in search_roots:
        for path in root.glob("*.yaml"):
            if path.stem == scenario_id:
                return path
    raise FileNotFoundError(f"scenario not found: {scenario_id}")


def load_scenario_id(scenario_id: str) -> Scenario:
    return load_scenario(find_scenario_path(scenario_id))
