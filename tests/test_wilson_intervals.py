import math

import pandas as pd

from scripts.add_wilson_intervals import add_intervals, wilson_interval


def test_wilson_interval_zero_successes_has_nonzero_upper_bound():
    low, high = wilson_interval(0, 48)

    assert low == 0.0
    assert 0.07 < high < 0.08


def test_add_intervals_adds_counts_and_bounds():
    frame = pd.DataFrame(
        [
            {
                "model_id": "shield",
                "episodes": 48,
                "material_misrepresentation_rate": 0.0,
            },
            {
                "model_id": "stress",
                "episodes": 48,
                "material_misrepresentation_rate": 0.125,
            },
        ]
    )

    enriched = add_intervals(frame, rate_columns=["material_misrepresentation_rate"])

    assert enriched.loc[0, "material_misrepresentation_rate_count"] == 0
    assert enriched.loc[1, "material_misrepresentation_rate_count"] == 6
    assert math.isfinite(enriched.loc[0, "material_misrepresentation_rate_wilson95_high"])
