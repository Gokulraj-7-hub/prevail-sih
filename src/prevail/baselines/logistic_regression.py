"""Logistic Regression baseline (FR-07). Required by the SIH PS as the point
of comparison for the World Model (FR-15).

Forecasting framing (see DECISIONS.md D-006): input is the *current* state's
own feature vector (the most recent historical window in a built sequence),
output is P(attack at the next window) -- the same one-step-ahead target the
World Model's derived attack probability is evaluated against, so the
baseline-vs-World-Model comparison in evaluation/ is apples-to-apples.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from prevail.evaluation.metrics import compute_binary_metrics


def current_state_input(seq_X: np.ndarray) -> np.ndarray:
    """Last timestep of each sequence = the current state at forecast time."""
    return seq_X[:, -1, :]


def train_logistic_regression(
    X_train: np.ndarray,
    y_train: np.ndarray,
    seed: int = 42,
    C: float = 1.0,
) -> tuple[StandardScaler, LogisticRegression]:
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    clf = LogisticRegression(
        C=C, class_weight="balanced", max_iter=2000, random_state=seed,
    )
    clf.fit(X_scaled, y_train)
    return scaler, clf


def evaluate_logistic_regression(
    scaler: StandardScaler, clf: LogisticRegression, X: np.ndarray, y: np.ndarray
) -> dict:
    X_scaled = scaler.transform(X)
    y_prob = clf.predict_proba(X_scaled)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    return compute_binary_metrics(y, y_pred, y_prob)


def save_baseline_artifacts(
    scaler: StandardScaler,
    clf: LogisticRegression,
    feature_columns: list[str],
    out_dir: str | Path,
) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"scaler": scaler, "model": clf, "feature_columns": feature_columns}, out_dir / "logistic_regression.joblib")

    coefs = dict(zip(feature_columns, clf.coef_[0].tolist()))
    top_coefs = dict(sorted(coefs.items(), key=lambda kv: abs(kv[1]), reverse=True)[:20])
    with open(out_dir / "coefficients_top20.txt", "w") as f:
        for name, val in top_coefs.items():
            f.write(f"{name}\t{val:.4f}\n")
