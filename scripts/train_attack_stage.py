#!/usr/bin/env python
"""Milestone 7: train the attack-stage interpretation classifier and demonstrate
the Phase 14 forecast table + ATT&CK mapping on one held-out attack scenario."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from sklearn.metrics import classification_report, confusion_matrix  # noqa: E402

from prevail.attack_mapping.mapper import AttackMapper  # noqa: E402
from prevail.attack_stage.interpret import build_forecast_table  # noqa: E402
from prevail.attack_stage.model import predict_stage_probs, save_stage_model, train_stage_classifier  # noqa: E402
from prevail.common.config import set_global_seed  # noqa: E402
from prevail.common.manifest import build_manifest, save_manifest  # noqa: E402
from prevail.common.schema import ATTACK_STAGES  # noqa: E402
from prevail.rollout.rollout import k_step_rollout_batch  # noqa: E402
from prevail.world_model.model import PrevailWorldModel  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
SEQ_LEN = 10


def main():
    set_global_seed(SEED)
    states = pd.read_parquet(ROOT / "data" / "processed" / "states_w5s.parquet")
    with open(ROOT / "data" / "processed" / "scenario_split.txt") as f:
        lines = f.read().splitlines()
    train_ids = lines[0].split(":", 1)[1].split(",")
    test_ids = lines[1].split(":", 1)[1].split(",")

    bundle = joblib.load(ROOT / "artifacts" / "world_model" / "scaler.joblib")
    feature_columns = bundle["feature_columns"]
    stage_to_idx = {s: i for i, s in enumerate(ATTACK_STAGES)}

    train_states = states[states["scenario_id"].isin(train_ids)]
    test_states = states[states["scenario_id"].isin(test_ids)]

    X_train = train_states[feature_columns].to_numpy(dtype=float)
    y_train = train_states["attack_stage"].map(stage_to_idx).to_numpy()
    X_test = test_states[feature_columns].to_numpy(dtype=float)
    y_test = test_states["attack_stage"].map(stage_to_idx).to_numpy()

    print(f"Train states: {X_train.shape}, test states: {X_test.shape}")
    scaler, clf = train_stage_classifier(X_train, y_train, seed=SEED)

    probs_test = predict_stage_probs(scaler, clf, X_test)
    y_pred = probs_test.argmax(axis=1)

    report = classification_report(
        y_test, y_pred, labels=list(range(len(ATTACK_STAGES))), target_names=ATTACK_STAGES,
        output_dict=True, zero_division=0,
    )
    cm = confusion_matrix(y_test, y_pred, labels=list(range(len(ATTACK_STAGES))))
    print("Classification report (test states):")
    for stage in ATTACK_STAGES:
        r = report[stage]
        print(f"  {stage:22s} precision={r['precision']:.3f} recall={r['recall']:.3f} "
              f"f1={r['f1-score']:.3f} support={int(r['support'])}")
    print(f"  overall accuracy: {report['accuracy']:.3f}")

    out_dir = ROOT / "artifacts" / "attack_stage"
    save_stage_model(scaler, clf, out_dir)
    manifest = build_manifest(
        experiment_name="attack_stage_classifier",
        dataset_version="synthetic-v1-seed42",
        feature_version="feature_registry-v1",
        model_version="rf-stage-classifier-v1",
        config={"n_estimators": 200, "max_depth": 8},
        seed=SEED,
        metrics={"classification_report": report, "confusion_matrix": cm.tolist()},
        extra={"data_source": "SYNTHETIC VALIDATION DATA - not a real-world benchmark result"},
    )
    save_manifest(manifest, out_dir / "manifest.json")

    # --- Demonstrate the Phase 14 forecast table on one held-out attack scenario ---
    wm_bundle = joblib.load(ROOT / "artifacts" / "world_model" / "scaler.joblib")
    wm_scaler = wm_bundle["scaler"]
    model = PrevailWorldModel(n_features=len(feature_columns))
    model.load_state_dict(torch.load(ROOT / "artifacts" / "world_model" / "world_model_v1.pt"))
    model.eval()

    demo_scenario = next(sid for sid in test_ids if "attack" in sid)
    sdf = states[states["scenario_id"] == demo_scenario].sort_values("window_id").reset_index(drop=True)
    # Start the rollout history AT the first non-benign window, so the model
    # has real precursor evidence of an in-progress attack to extrapolate
    # from (see docs/experiments/attack-stage.md for the alternate case --
    # rolling out from purely-benign pre-attack history -- which is a much
    # harder, honestly-reported near-miss: there is no signal yet to detect).
    first_attack_idx = int(sdf[sdf["attack_stage"] != "benign"].index.min())
    start_t = min(first_attack_idx, max(0, len(sdf) - SEQ_LEN))
    history = sdf.loc[start_t:start_t + SEQ_LEN - 1, feature_columns].to_numpy(dtype=float)[None, :, :]

    rollout_out = k_step_rollout_batch(model, wm_scaler, history, K=5)
    mapper = AttackMapper()
    table = build_forecast_table(scaler, clf, rollout_out["states"][0], mapper)

    print(f"\nDemo forecast table (scenario {demo_scenario}, rollout starting at window {start_t + SEQ_LEN}):")
    for row in table:
        tactic = row["attck_tactic"]["name"] if row["attck_tactic"] else "-"
        print(f"  T+{row['step']} {row['predicted_stage']:22s} p={row['stage_probability']:.2f} "
              f"P(attack)={row['p_attack']:.2f}  ATT&CK: {tactic} (confidence={row['attck_mapping_confidence']})")

    with open(out_dir / "demo_forecast_table.json", "w") as f:
        json.dump({"scenario_id": demo_scenario, "start_window": start_t + SEQ_LEN, "table": table}, f, indent=2)
    print(f"\nSaved -> {out_dir}")


if __name__ == "__main__":
    main()
