import pandas as pd

from segym.analysis.metrics import aggregate_by_model


def test_aggregate_by_model_includes_best_of_n_rates_when_available():
    df = pd.DataFrame(
        [
            {
                "model_id": "best_of_n_utility",
                "condition": "neutral",
                "scenario_id": "a",
                "settled": True,
                "client_utility": 1.0,
                "episode_has_material_violation": True,
                "episode_has_severe_violation": True,
                "material_violation_count": 1,
                "safe_candidate_available": True,
                "selected_unsafe_despite_safe": True,
            },
            {
                "model_id": "best_of_n_utility",
                "condition": "neutral",
                "scenario_id": "b",
                "settled": True,
                "client_utility": 1.0,
                "episode_has_material_violation": False,
                "episode_has_severe_violation": False,
                "material_violation_count": 0,
                "safe_candidate_available": True,
                "selected_unsafe_despite_safe": False,
            },
        ]
    )

    summary = aggregate_by_model(df)

    assert summary.loc[0, "safe_candidate_available_rate"] == 1.0
    assert summary.loc[0, "selected_unsafe_despite_safe_rate"] == 0.5


def test_aggregate_by_model_includes_shield_rates_when_available():
    df = pd.DataFrame(
        [
            {
                "model_id": "shielded",
                "condition": "llm_shield",
                "scenario_id": "a",
                "settled": True,
                "client_utility": 1.0,
                "episode_has_material_violation": False,
                "episode_has_severe_violation": False,
                "material_violation_count": 0,
                "shield_triggered": True,
                "shield_trigger_count": 2,
            },
            {
                "model_id": "shielded",
                "condition": "llm_shield",
                "scenario_id": "b",
                "settled": True,
                "client_utility": 0.8,
                "episode_has_material_violation": False,
                "episode_has_severe_violation": False,
                "material_violation_count": 0,
                "shield_triggered": False,
                "shield_trigger_count": 0,
            },
        ]
    )

    summary = aggregate_by_model(df)

    assert summary.loc[0, "shield_triggered_rate"] == 0.5
    assert summary.loc[0, "mean_shield_trigger_count"] == 1.0


def test_aggregate_by_model_includes_llm_parse_failure_rates_when_available():
    df = pd.DataFrame(
        [
            {
                "model_id": "llm",
                "condition": "zero_shot",
                "scenario_id": "a",
                "settled": False,
                "client_utility": 0.0,
                "episode_has_material_violation": False,
                "episode_has_severe_violation": False,
                "material_violation_count": 0,
                "llm_parse_failed": True,
                "llm_parse_failure_count": 2,
            },
            {
                "model_id": "llm",
                "condition": "zero_shot",
                "scenario_id": "b",
                "settled": True,
                "client_utility": 1.0,
                "episode_has_material_violation": False,
                "episode_has_severe_violation": False,
                "material_violation_count": 0,
                "llm_parse_failed": False,
                "llm_parse_failure_count": 0,
            },
        ]
    )

    summary = aggregate_by_model(df)

    assert summary.loc[0, "llm_parse_failed_rate"] == 0.5
    assert summary.loc[0, "mean_llm_parse_failure_count"] == 1.0
