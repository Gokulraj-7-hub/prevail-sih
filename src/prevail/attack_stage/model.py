"""Attack-stage interpretation model (Phase 17/FR-12): a strictly downstream
layer over *states* (real or World-Model-predicted) -- architecturally
separate from the World Model's own auxiliary head (see architecture.md
module map: "attack_stage/ ... Must NOT ... Treat a predicted state as ground
truth without provenance tag"). Trained independently on ground-truth states
so it can be applied uniformly to observed states and rollout output.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from prevail.common.schema import ATTACK_STAGES


def train_stage_classifier(
    X: np.ndarray, y_stage: np.ndarray, seed: int = 42, n_estimators: int = 200
) -> tuple[StandardScaler, RandomForestClassifier]:
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    clf = RandomForestClassifier(
        n_estimators=n_estimators, max_depth=8, class_weight="balanced_subsample",
        random_state=seed, n_jobs=-1,
    )
    clf.fit(X_scaled, y_stage)
    return scaler, clf


def predict_stage_probs(scaler: StandardScaler, clf: RandomForestClassifier, X: np.ndarray) -> np.ndarray:
    """Returns (n, n_stages) probabilities in prevail.common.schema.ATTACK_STAGES order."""
    X_scaled = scaler.transform(X)
    probs = clf.predict_proba(X_scaled)
    # sklearn orders columns by clf.classes_ -- realign to our canonical order.
    aligned = np.zeros((X.shape[0], len(ATTACK_STAGES)))
    for i, cls in enumerate(clf.classes_):
        aligned[:, cls] = probs[:, i]
    return aligned


def save_stage_model(scaler: StandardScaler, clf: RandomForestClassifier, out_dir: str | Path) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"scaler": scaler, "model": clf}, out_dir / "stage_classifier.joblib")


def load_stage_model(out_dir: str | Path) -> tuple[StandardScaler, RandomForestClassifier]:
    bundle = joblib.load(Path(out_dir) / "stage_classifier.joblib")
    return bundle["scaler"], bundle["model"]
