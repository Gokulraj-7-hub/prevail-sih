"""Temporal evidence (Phase 19): which historical windows in the input
sequence contributed most to the World Model's next-state prediction.

Method: occlusion. Replace one historical window at a time with the
sequence's own mean window, re-run the model, and measure how much the
prediction changes. A window whose removal changes the prediction a lot is
"important evidence" -- explicitly not a causal claim, just sensitivity of
the model's own output to that input (master prompt Phase 19 discipline).
"""
from __future__ import annotations

import numpy as np
import torch

from prevail.world_model.model import PrevailWorldModel
from prevail.world_model.train import FeatureScaler


@torch.no_grad()
def temporal_window_importance(
    model: PrevailWorldModel,
    scaler: FeatureScaler,
    history: np.ndarray,  # (seq_len, n_features), raw units
) -> list[dict]:
    model.eval()
    seq_len = history.shape[0]
    mean_window = history.mean(axis=0)

    def predict(h: np.ndarray) -> np.ndarray:
        h_s = scaler.transform(h[None, :, :])
        out = model(torch.tensor(h_s, dtype=torch.float32))
        return out["next_state"].numpy()[0]

    baseline_pred = predict(history)

    importances = []
    for t in range(seq_len):
        perturbed = history.copy()
        perturbed[t] = mean_window
        perturbed_pred = predict(perturbed)
        delta = float(np.linalg.norm(baseline_pred - perturbed_pred))
        importances.append({"relative_position": t - seq_len, "importance": delta})  # e.g. -3 = "T-3"

    max_imp = max(i["importance"] for i in importances) or 1.0
    for i in importances:
        i["importance_normalized"] = i["importance"] / max_imp
        i["label"] = f"T{i['relative_position']}" if i["relative_position"] != 0 else "T"

    return sorted(importances, key=lambda d: -d["importance"])
