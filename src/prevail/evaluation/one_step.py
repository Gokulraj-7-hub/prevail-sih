"""One-step evaluation (master prompt Phase 12): prove S_t -> Ŝ_{t+1} works
before attempting K-step rollout."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score, brier_score_loss


def feature_level_error(
    y_true: np.ndarray, y_pred: np.ndarray, feature_columns: list[str], feature_std: np.ndarray | None = None
) -> dict:
    """Reports both raw-unit and standardized (error / train-set std) MAE/MSE.

    Raw-unit MSE is dominated by naturally huge-scale features (e.g. a rolling
    variance of byte counts) and is NOT a fair way to rank "worst" features --
    a feature with std ~1e4 will always have a bigger raw MSE than one with
    std ~1, independent of how well the model actually predicts it (see
    DECISIONS.md D-008). Ranking uses standardized error when std is given.
    """
    mae = np.abs(y_true - y_pred).mean(axis=0)
    mse = ((y_true - y_pred) ** 2).mean(axis=0)

    if feature_std is not None:
        std = np.where(feature_std < 1e-8, 1.0, feature_std)
        mae_norm = mae / std
        mse_norm = mse / (std ** 2)
    else:
        mae_norm = mae
        mse_norm = mse

    per_feature = {
        feature_columns[i]: {
            "mae": float(mae[i]), "mse": float(mse[i]),
            "mae_normalized": float(mae_norm[i]), "mse_normalized": float(mse_norm[i]),
        }
        for i in range(len(feature_columns))
    }
    worst = sorted(per_feature.items(), key=lambda kv: kv[1]["mse_normalized"], reverse=True)[:10]
    return {
        "overall_mae": float(mae.mean()),
        "overall_mse": float(mse.mean()),
        "overall_mae_normalized": float(mae_norm.mean()),
        "overall_mse_normalized": float(mse_norm.mean()),
        "worst_10_features_by_normalized_mse": dict(worst),
    }


def state_similarity(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Cosine similarity between predicted and true state vectors."""
    num = (y_true * y_pred).sum(axis=1)
    denom = np.linalg.norm(y_true, axis=1) * np.linalg.norm(y_pred, axis=1)
    denom[denom < 1e-8] = 1e-8
    cos_sim = num / denom
    return {"mean_cosine_similarity": float(cos_sim.mean()), "min_cosine_similarity": float(cos_sim.min())}


def attack_stage_accuracy(y_stage_true: np.ndarray, stage_pred_probs: np.ndarray) -> dict:
    y_stage_pred = stage_pred_probs.argmax(axis=1)
    acc = accuracy_score(y_stage_true, y_stage_pred)
    return {"accuracy": float(acc)}


def calibration(y_binary_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> dict:
    """Reliability: Brier score + binned reliability diagram data."""
    brier = brier_score_loss(y_binary_true, y_prob)
    bins = np.linspace(0, 1, n_bins + 1)
    bin_ids = np.digitize(y_prob, bins) - 1
    bin_ids = np.clip(bin_ids, 0, n_bins - 1)
    reliability = []
    for b in range(n_bins):
        mask = bin_ids == b
        if mask.sum() == 0:
            continue
        reliability.append({
            "bin_center": float((bins[b] + bins[b + 1]) / 2),
            "predicted_mean": float(y_prob[mask].mean()),
            "observed_rate": float(y_binary_true[mask].mean()),
            "count": int(mask.sum()),
        })
    return {"brier_score": float(brier), "reliability_bins": reliability}


def temporal_consistency(y_true_seq: np.ndarray, y_pred_seq: np.ndarray) -> dict:
    """Correlation between the true and predicted direction of change vs the
    previous timestep's last known state -- a crude sanity check that the
    model tracks the *trend*, not just the unconditional mean."""
    true_delta = y_true_seq  # already delta-like for change-sensitive features; caller passes deltas
    pred_delta = y_pred_seq
    if true_delta.std() < 1e-8 or pred_delta.std() < 1e-8:
        return {"trend_correlation": 0.0}
    corr = float(np.corrcoef(true_delta.flatten(), pred_delta.flatten())[0, 1])
    return {"trend_correlation": corr}
