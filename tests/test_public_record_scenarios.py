from pathlib import Path

from segym.scenario import load_scenario, load_scenario_id
from segym.validation import validate_path


SPLIT = Path("data/splits/public_record_grounded_v0_1_12.txt")


def test_public_record_grounded_split_validates():
    paths = [Path(line.strip()) for line in SPLIT.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(paths) == 12
    for path in paths:
        report = validate_path(path)
        assert report.ok, f"{path}: {report.errors}"
        scenario = load_scenario(path)
        assert scenario.source_type == "public_case_syntheticized"
        assert len(scenario.facts) >= 3


def test_public_record_scenarios_load_by_id():
    scenario = load_scenario_id("liebeck_hot_coffee_public_001")
    assert scenario.source_type == "public_case_syntheticized"
