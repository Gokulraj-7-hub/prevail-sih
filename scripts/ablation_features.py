#!/usr/bin/env python
"""Experiments E/F/G: flow-only vs packet-only vs flow+packet feature ablation
(master prompt Phase 19), using the Logistic Regression baseline (cheap,
fast, isolates the feature-family effect from World Model architecture
choices -- a confound-free ablation)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from prevail.baselines.logistic_regression import (  # noqa: E402
    current_state_input, evaluate_logistic_regression, train_logistic_regression,
)
from prevail.common.config import set_global_seed  # noqa: E402
from prevail.common.schema import FLOW_FEATURES, PACKET_FEATURES, TEMPORAL_FEATURES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SEED = 42

FAMILIES = {
    "flow_only": FLOW_FEATURES,
    "packet_only": PACKET_FEATURES,
    "temporal_only": TEMPORAL_FEATURES,
    "flow_plus_packet": FLOW_FEATURES + PACKET_FEATURES,
    "all_features (baseline default)": FLOW_FEATURES + PACKET_FEATURES + TEMPORAL_FEATURES,
}


def main():
    set_global_seed(SEED)
    processed = ROOT / "data" / "processed"
    train_npz = np.load(processed / "sequences_w5s_L10_train.npz", allow_pickle=True)
    test_npz = np.load(processed / "sequences_w5s_L10_test.npz", allow_pickle=True)
    all_columns = list(train_npz["feature_columns"])

    X_train_full = current_state_input(train_npz["X"])
    y_train = train_npz["y_label"]
    X_test_full = current_state_input(test_npz["X"])
    y_test = test_npz["y_label"]

    results = {}
    for name, family_features in FAMILIES.items():
        idx = [i for i, c in enumerate(all_columns) if c.split("__", 1)[1] in family_features]
        X_train = X_train_full[:, idx]
        X_test = X_test_full[:, idx]

        scaler, clf = train_logistic_regression(X_train, y_train, seed=SEED, C=1.0)
        test_metrics = evaluate_logistic_regression(scaler, clf, X_test, y_test)
        results[name] = {"n_features": len(idx), "test_metrics": test_metrics}
        print(f"{name:35s} n_features={len(idx):3d}  "
              f"F1={test_metrics['f1']:.3f}  ROC-AUC={test_metrics['roc_auc']:.3f}  "
              f"FPR={test_metrics['false_positive_rate']:.3f}")

    out_dir = ROOT / "artifacts" / "ablation"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "feature_family_ablation.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved -> {out_dir / 'feature_family_ablation.json'}")


if __name__ == "__main__":
    main()
