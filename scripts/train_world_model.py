#!/usr/bin/env python
"""Milestone 5: train World Model V1, run one-step evaluation (Phase 10, 12)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402

from prevail.common.config import set_global_seed  # noqa: E402
from prevail.common.manifest import build_manifest, save_manifest  # noqa: E402
from prevail.evaluation.one_step import (  # noqa: E402
    attack_stage_accuracy, calibration, feature_level_error, state_similarity, temporal_consistency,
)
from prevail.sequences.split import scenario_train_test_split  # noqa: E402
from prevail.world_model.train import train_world_model  # noqa: E402

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

    # Further split train scenarios into train/val (never touching test scenarios)
    scenario_meta = pd.read_csv(ROOT / "data" / "metadata" / "scenarios.csv")
    train_scenario_ids = set(train_npz["scenario_id"].tolist())
    train_meta = scenario_meta[scenario_meta["scenario_id"].isin(train_scenario_ids)]
    fit_ids, val_ids = scenario_train_test_split(train_meta, test_fraction=0.2, seed=SEED)

    sid = train_npz["scenario_id"]
    fit_mask = np.isin(sid, fit_ids)
    val_mask = np.isin(sid, val_ids)

    X_fit, y_fit, ystage_fit = train_npz["X"][fit_mask], train_npz["y"][fit_mask], train_npz["y_stage"][fit_mask]
    X_val, y_val, ystage_val = train_npz["X"][val_mask], train_npz["y"][val_mask], train_npz["y_stage"][val_mask]
    X_test, y_test, ystage_test = test_npz["X"], test_npz["y"], test_npz["y_stage"]
    ylabel_test = test_npz["y_label"]

    print(f"fit={X_fit.shape} val={X_val.shape} test={X_test.shape}")

    model, scaler, history = train_world_model(
        X_fit, y_fit, ystage_fit, X_val, y_val, ystage_val,
        n_features=len(feature_columns), seed=SEED,
    )
    print(f"Training done: {history['epochs_run']} epochs, best val loss {history['best_val_loss']:.4f}")

    # One-step evaluation on the held-out TEST scenarios (never used for fit/val).
    model.eval()
    X_test_s = scaler.transform(X_test)
    with torch.no_grad():
        out = model(torch.tensor(X_test_s, dtype=torch.float32))
    pred_state_s = out["next_state"].numpy()
    pred_state = scaler.inverse_transform_vec(pred_state_s)
    stage_probs = torch.softmax(out["stage_logits"], dim=1).numpy()
    p_attack = 1.0 - stage_probs[:, 0]  # index 0 == "benign" in ATTACK_STAGES

    feat_err = feature_level_error(y_test, pred_state, feature_columns, feature_std=scaler.std_)
    sim = state_similarity(y_test, pred_state)
    stage_acc = attack_stage_accuracy(ystage_test, stage_probs)
    calib = calibration(ylabel_test, p_attack)
    trend = temporal_consistency(y_test - X_test[:, -1, :], pred_state - X_test[:, -1, :])

    results = {
        "feature_level_error": feat_err,
        "state_similarity": sim,
        "attack_stage_accuracy": stage_acc,
        "calibration": calib,
        "temporal_consistency": trend,
        "training_history": {k: v for k, v in history.items() if k in ("best_val_loss", "epochs_run")},
    }
    print("One-step eval:", {k: v for k, v in results.items() if k != "calibration"})

    out_dir = ROOT / "artifacts" / "world_model"
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_dir / "world_model_v1.pt")
    joblib.dump({"scaler": scaler, "feature_columns": feature_columns}, out_dir / "scaler.joblib")

    manifest = build_manifest(
        experiment_name="C_temporal_transformer_one_step",
        dataset_version="synthetic-v1-seed42",
        feature_version="feature_registry-v1",
        model_version="prevail-world-model-v1",
        config={
            "window_size_s": WINDOW_SIZE_S, "seq_len": SEQ_LEN, "d_model": 64,
            "n_heads": 4, "n_layers": 3, "dropout": 0.1,
        },
        seed=SEED,
        metrics=results,
        extra={"data_source": "SYNTHETIC VALIDATION DATA - not a real-world benchmark result"},
    )
    save_manifest(manifest, out_dir / "manifest.json")
    print(f"Saved World Model artifacts + manifest to {out_dir}")


if __name__ == "__main__":
    main()
