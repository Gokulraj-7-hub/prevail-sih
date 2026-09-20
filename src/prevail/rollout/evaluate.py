"""K-step rollout evaluation (master prompt Phase 16/17): error accumulation
across K, and calibrated future-attack-probability output."""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from prevail.common.schema import ATTACK_STAGES
from prevail.rollout.rollout import k_step_rollout_batch
from prevail.world_model.model import PrevailWorldModel
from prevail.world_model.train import FeatureScaler

STAGE_TO_IDX = {s: i for i, s in enumerate(ATTACK_STAGES)}


def build_trajectories(
    states: pd.DataFrame, scenario_ids: list[str], feature_columns: list[str], seq_len: int, K: int
) -> dict[str, np.ndarray]:
    """All valid (history, future) pairs within the given scenarios, with
    enough future windows in-scenario to evaluate all K steps."""
    hist_list, future_states_list, future_stage_list, future_label_list, sid_list, start_t_list = [], [], [], [], [], []

    for sid in scenario_ids:
        sdf = states[states["scenario_id"] == sid].sort_values("window_id").reset_index(drop=True)
        feats = sdf[feature_columns].to_numpy(dtype=float)
        stages = sdf["attack_stage"].map(STAGE_TO_IDX).to_numpy()
        labels = sdf["attack_label"].to_numpy()
        n = len(sdf)
        for t in range(0, n - seq_len - K + 1):
            hist_list.append(feats[t:t + seq_len])
            future_states_list.append(feats[t + seq_len: t + seq_len + K])
            future_stage_list.append(stages[t + seq_len: t + seq_len + K])
            future_label_list.append(labels[t + seq_len: t + seq_len + K])
            sid_list.append(sid)
            start_t_list.append(t)

    return {
        "history": np.stack(hist_list),
        "future_states": np.stack(future_states_list),
        "future_stage": np.stack(future_stage_list),
        "future_label": np.stack(future_label_list),
        "scenario_id": np.array(sid_list, dtype=object),
        "start_t": np.array(start_t_list, dtype=int),
    }


def evaluate_k_step_error_accumulation(
    model: PrevailWorldModel,
    scaler: FeatureScaler,
    trajectories: dict[str, np.ndarray],
    K: int,
) -> dict:
    """Per-step normalized MSE / cosine similarity / stage accuracy / P(attack)
    calibration, computed independently at each rollout step 1..K, to show
    whether/how fast error accumulates (master prompt: 'do not assume K=5 is
    always best; measure error accumulation')."""
    out = k_step_rollout_batch(model, scaler, trajectories["history"], K)
    pred_states = out["states"]         # (n_traj, K, n_features)
    pred_stage_probs = out["stage_probs"]  # (n_traj, K, n_stages)

    true_states = trajectories["future_states"]
    true_stage = trajectories["future_stage"]
    true_label = trajectories["future_label"]

    std = np.where(scaler.std_ < 1e-8, 1.0, scaler.std_)

    per_step = []
    for k in range(K):
        err = pred_states[:, k, :] - true_states[:, k, :]
        norm_mse = float(np.mean((err / std) ** 2))
        num = (pred_states[:, k, :] * true_states[:, k, :]).sum(axis=1)
        denom = np.linalg.norm(pred_states[:, k, :], axis=1) * np.linalg.norm(true_states[:, k, :], axis=1)
        denom[denom < 1e-8] = 1e-8
        cos_sim = float(np.mean(num / denom))

        pred_stage = pred_stage_probs[:, k, :].argmax(axis=1)
        stage_acc = float((pred_stage == true_stage[:, k]).mean())

        p_attack = 1.0 - pred_stage_probs[:, k, STAGE_TO_IDX["benign"]]
        pred_label = (p_attack >= 0.5).astype(int)
        tp = int(((pred_label == 1) & (true_label[:, k] == 1)).sum())
        fp = int(((pred_label == 1) & (true_label[:, k] == 0)).sum())
        fn = int(((pred_label == 0) & (true_label[:, k] == 1)).sum())
        tn = int(((pred_label == 0) & (true_label[:, k] == 0)).sum())
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        fpr = fp / (fp + tn) if (fp + tn) else 0.0

        per_step.append({
            "k": k + 1,
            "normalized_mse": norm_mse,
            "cosine_similarity": cos_sim,
            "stage_accuracy": stage_acc,
            "mean_p_attack": float(p_attack.mean()),
            "precision": precision, "recall": recall, "f1": f1, "false_positive_rate": fpr,
        })

    return {"n_trajectories": int(pred_states.shape[0]), "per_step": per_step}
