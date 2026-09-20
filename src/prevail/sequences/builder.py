"""Chronological state-sequence construction (master prompt Phase 6/7, FR-06).

[S0..S_{L-1}] -> S_L, sliding within a single scenario only -- a sequence
never crosses a scenario_id boundary, which would silently blend two
unrelated capture sessions into one fake temporal continuity.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from prevail.common.schema import ATTACK_STAGES
from prevail.states.builder import feature_columns


def build_sequences(
    states: pd.DataFrame,
    seq_len: int = 10,
    families: tuple[str, ...] = ("flow", "packet", "temporal"),
) -> dict[str, np.ndarray]:
    """Returns dict with:
      X: (n_samples, seq_len, n_features) -- input history
      y: (n_samples, n_features) -- target next-state feature vector
      y_stage: (n_samples,) int -- target window's attack-stage index
      y_label: (n_samples,) int -- target window's binary attack label
      scenario_id: (n_samples,) str -- which scenario each sample came from
      target_window_id: (n_samples,) int
    """
    cols = feature_columns(states, families)
    stage_to_idx = {s: i for i, s in enumerate(ATTACK_STAGES)}

    X_list, y_list, y_stage_list, y_label_list, sid_list, twid_list = [], [], [], [], [], []

    for scenario_id, sdf in states.groupby("scenario_id", sort=True):
        sdf = sdf.sort_values("window_id").reset_index(drop=True)
        feats = sdf[cols].to_numpy(dtype=float)
        n = len(sdf)
        for start in range(0, n - seq_len):
            X_list.append(feats[start:start + seq_len])
            target_idx = start + seq_len
            y_list.append(feats[target_idx])
            y_stage_list.append(stage_to_idx[sdf.loc[target_idx, "attack_stage"]])
            y_label_list.append(int(sdf.loc[target_idx, "attack_label"]))
            sid_list.append(scenario_id)
            twid_list.append(int(sdf.loc[target_idx, "window_id"]))

    return {
        "X": np.stack(X_list) if X_list else np.zeros((0, seq_len, len(cols))),
        "y": np.stack(y_list) if y_list else np.zeros((0, len(cols))),
        "y_stage": np.array(y_stage_list, dtype=int),
        "y_label": np.array(y_label_list, dtype=int),
        "scenario_id": np.array(sid_list, dtype=object),
        "target_window_id": np.array(twid_list, dtype=int),
        "feature_columns": cols,
    }
