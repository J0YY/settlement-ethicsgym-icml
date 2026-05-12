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
