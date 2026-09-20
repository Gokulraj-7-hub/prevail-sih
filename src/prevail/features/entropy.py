from __future__ import annotations

import numpy as np
import pandas as pd


def shannon_entropy(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    counts = series.value_counts(normalize=True).to_numpy()
    counts = counts[counts > 0]
    return float(-(counts * np.log2(counts)).sum())
