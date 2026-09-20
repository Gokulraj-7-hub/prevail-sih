"""Temporal windowing (master prompt Phase 6). Window size is an experimental
hyperparameter, default 5s -- see docs/architecture/data-contract.md Sec 4."""
from __future__ import annotations

import pandas as pd

DEFAULT_WINDOW_SIZE_S = 5.0


def assign_windows(df: pd.DataFrame, window_size_s: float = DEFAULT_WINDOW_SIZE_S) -> pd.DataFrame:
    """Adds window_id, window_start, window_end columns.

    Windows are anchored per-scenario at that scenario's own minimum timestamp,
    so window boundaries never depend on cross-scenario timing (which would be
    a leakage risk if scenarios were later concatenated on a shared global clock).
    """
    df = df.copy()
    scenario_start = df.groupby("scenario_id")["timestamp"].transform("min")
    rel_t = df["timestamp"] - scenario_start
    df["window_id"] = (rel_t // window_size_s).astype(int)
    df["window_start"] = scenario_start + df["window_id"] * window_size_s
    df["window_end"] = df["window_start"] + window_size_s
    return df
