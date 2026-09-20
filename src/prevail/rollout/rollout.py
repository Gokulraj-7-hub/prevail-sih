"""K-step autoregressive rollout (master prompt Phase 16, FR-10).

state = S_t
for k in range(K):
    predicted_state = world_model(history)
    history = history[1:] + [predicted_state]   # slide window
"""
from __future__ import annotations

import numpy as np
import torch

from prevail.world_model.model import PrevailWorldModel
from prevail.world_model.train import FeatureScaler


@torch.no_grad()
def k_step_rollout_batch(
    model: PrevailWorldModel,
    scaler: FeatureScaler,
    initial_histories: np.ndarray,  # (n_traj, seq_len, n_features), raw units
    K: int,
) -> dict[str, np.ndarray]:
    """Vectorized K-step rollout for a batch of independent trajectories.

    Returns:
      states: (n_traj, K, n_features) raw-unit predicted states, one per step.
      stage_probs: (n_traj, K, n_stages) attack-stage probability at each step,
        taken from the model's own auxiliary head evaluated on the history
        that produced that step's prediction (i.e. P(stage at t+k) using only
        information available up to t+k-1's predicted state).
    """
    model.eval()
    history = initial_histories.copy()  # raw units, will be updated with predictions
    n_traj, seq_len, n_features = history.shape

    all_states = []
    all_stage_probs = []

    for _ in range(K):
        history_s = scaler.transform(history)
        out = model(torch.tensor(history_s, dtype=torch.float32))
        next_state_s = out["next_state"].numpy()
        next_state = scaler.inverse_transform_vec(next_state_s)
        stage_probs = torch.softmax(out["stage_logits"], dim=1).numpy()

        all_states.append(next_state)
        all_stage_probs.append(stage_probs)

        history = np.concatenate([history[:, 1:, :], next_state[:, None, :]], axis=1)

    return {
        "states": np.stack(all_states, axis=1),
        "stage_probs": np.stack(all_stage_probs, axis=1),
    }
