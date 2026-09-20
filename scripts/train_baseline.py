#!/usr/bin/env python
"""Milestone 4: train + evaluate the Logistic Regression baseline (FR-07)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from prevail.baselines.logistic_regression import (  # noqa: E402
    current_state_input,
    evaluate_logistic_regression,
    save_baseline_artifacts,
    train_logistic_regression,
)
from prevail.common.config import set_global_seed  # noqa: E402
from prevail.common.manifest import build_manifest, save_manifest  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
WINDOW_SIZE_S = 5
SEQ_LEN = 10


def main():
    set_global_seed(SEED)
    processed = ROOT / "data" / "processed"
    train_npz = np.load(processed / f"sequences_w{WINDOW_SIZE_S}s_L{SEQ_LEN}_train.npz", allow_pickle=True)
    test_npz = np.load(processed / f"sequences_w{WINDOW_SIZE_S}s_L{SEQ_LEN}_test.npz", allow_pickle=True)

    feature_columns = list(train_npz["feature_columns"])
    X_train = current_state_input(train_npz["X"])
    y_train = train_npz["y_label"]
    X_test = current_state_input(test_npz["X"])
    y_test = test_npz["y_label"]

    print(f"Train: {X_train.shape}, positive rate {y_train.mean():.3f}")
    print(f"Test:  {X_test.shape}, positive rate {y_test.mean():.3f}")

    scaler, clf = train_logistic_regression(X_train, y_train, seed=SEED, C=1.0)

    train_metrics = evaluate_logistic_regression(scaler, clf, X_train, y_train)
    test_metrics = evaluate_logistic_regression(scaler, clf, X_test, y_test)

    print("Train metrics:", train_metrics)
    print("Test metrics: ", test_metrics)

    out_dir = ROOT / "artifacts" / "baseline"
    save_baseline_artifacts(scaler, clf, feature_columns, out_dir)

    manifest = build_manifest(
        experiment_name="A_logistic_regression_baseline",
        dataset_version="synthetic-v1-seed42",
        feature_version="feature_registry-v1",
        model_version="sklearn-logreg-v1",
        config={"C": 1.0, "class_weight": "balanced", "window_size_s": WINDOW_SIZE_S, "seq_len": SEQ_LEN},
        seed=SEED,
        metrics={"train": train_metrics, "test": test_metrics},
        extra={"data_source": "SYNTHETIC VALIDATION DATA - not a real-world benchmark result"},
    )
    save_manifest(manifest, out_dir / "manifest.json")
    print(f"Saved baseline artifacts + manifest to {out_dir}")


if __name__ == "__main__":
    main()
