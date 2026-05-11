from pathlib import Path

from segym.scenario import load_scenario
from segym.validation import validate_path, validate_scenario


SCENARIO = Path("data/scenarios/seed/pi_policy_limits_001.yaml")


def test_forbidden_patterns_reference_existing_facts():
    scenario = load_scenario(SCENARIO)
    fact_ids = {fact.fact_id for fact in scenario.facts}
    assert all(pattern.maps_to_fact_id in fact_ids for pattern in scenario.forbidden_patterns)


def test_reservation_values_coherent():
    scenario = load_scenario(SCENARIO)
    report = validate_scenario(scenario)
    assert not report.errors


def test_sample_gold_labels_valid():
    report = validate_path(SCENARIO)
    assert not report.errors


def test_all_seed_scenarios_validate():
    reports = [validate_path(path) for path in Path("data/scenarios/seed").glob("*.yaml")]
    errors = [err for report in reports for err in report.errors]
    assert not errors

