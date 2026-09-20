"""Defensive what-if simulator (Phase 20, FR-17):

Current state -> Baseline forecast -> Intervention selector ->
Modified simulated state -> World Model -> Counterfactual forecast

Only ever modifies the *current* (most recent) window in a history -- matching
the master prompt's own architecture diagram, and keeping every earlier
window (and therefore every delta/rolling temporal feature computed from it)
identical to the real observed baseline. Language throughout is
forecast-only: "the model forecasts a lower probability under the simulated
intervention," never a causal prevention claim (master prompt Sec 2.5).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from prevail.features.temporal import ROLLING_WINDOW
from prevail.intervention.interventions import InterventionSpec
from prevail.states.builder import compute_window_row


def _window_bounds(scenario_start: float, window_id: int, window_size_s: float) -> tuple[float, float]:
    start = scenario_start + window_id * window_size_s
    return start, start + window_size_s


def compute_modified_current_state(
    scenario_packets: pd.DataFrame,
    scenario_states: pd.DataFrame,  # this scenario's rows only, sorted by window_id, from states/builder output
    target_window_id: int,
    window_size_s: float,
    spec: InterventionSpec,
    feature_columns: list[str],
) -> np.ndarray:
    """Recomputes ONLY target_window_id's feature vector, using the same
    prior-window context (prev flow features, trailing bytes) as the real
    pipeline, but with the intervention's packet filter applied to that
    window's packets before feature extraction."""
    scenario_id = scenario_states["scenario_id"].iloc[0]
    scenario_start = float(scenario_packets["timestamp"].min())

    prior = scenario_states[scenario_states["window_id"] < target_window_id].sort_values("window_id")
    prev_flow_feats = None
    if len(prior):
        last_row = prior.iloc[-1]
        prev_flow_feats = {c.split("__", 1)[1]: last_row[c] for c in scenario_states.columns if c.startswith("flow__")}
    trailing_bytes = prior["flow__bytes_sum"].tail(ROLLING_WINDOW).tolist()

    win_start, win_end = _window_bounds(scenario_start, target_window_id, window_size_s)
    window_pkts = scenario_packets[
        (scenario_packets["scenario_id"] == scenario_id)
        & (scenario_packets["timestamp"] >= win_start)
        & (scenario_packets["timestamp"] < win_end)
    ]

    filtered_pkts = spec.filter_fn(window_pkts)
    row, _ = compute_window_row(filtered_pkts, prev_flow_feats, window_size_s, trailing_bytes, has_packet_data=True)
    return np.array([float(row.get(c, 0.0) or 0.0) for c in feature_columns])


def build_counterfactual_history(
    baseline_history: np.ndarray,  # (seq_len, n_features)
    modified_current_state: np.ndarray,  # (n_features,)
) -> np.ndarray:
    modified = baseline_history.copy()
    modified[-1] = modified_current_state
    return modified


OOD_WARN_THRESHOLD = 1.15  # ~92nd percentile of mean|z| across all real synthetic states (D-010)


def out_of_distribution_score(state: np.ndarray, train_mean: np.ndarray, train_std: np.ndarray) -> float:
    """Mean |z-score| across features, relative to the World Model's own
    training distribution. A counterfactual state built by aggressively
    filtering packets out of a window is a distribution shift the model was
    never trained on -- this is a cheap sanity flag, not a rigorous OOD
    detector (see DECISIONS.md D-010 for why it exists and its limits)."""
    std = np.where(train_std < 1e-8, 1.0, train_std)
    return float(np.mean(np.abs((state - train_mean) / std)))


def is_out_of_distribution(state: np.ndarray, train_mean: np.ndarray, train_std: np.ndarray) -> bool:
    return out_of_distribution_score(state, train_mean, train_std) > OOD_WARN_THRESHOLD
