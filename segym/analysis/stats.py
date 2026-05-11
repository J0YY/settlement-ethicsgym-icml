from __future__ import annotations

import numpy as np


def bootstrap_mean_ci(values, n_boot: int = 1000, seed: int = 0) -> tuple[float, float, float]:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return 0.0, 0.0, 0.0
    rng = np.random.default_rng(seed)
    means = [rng.choice(arr, size=arr.size, replace=True).mean() for _ in range(n_boot)]
    return float(arr.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))

