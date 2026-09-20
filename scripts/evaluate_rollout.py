#!/usr/bin/env python
"""Milestone 6: K-step rollout evaluation, K in {1,2,3,5} (Phase 16)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import joblib  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402

from prevail.rollout.evaluate import build_trajectories, evaluate_k_step_error_accumulation  # noqa: E402
from prevail.world_model.model import PrevailWorldModel  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
K_VALUES = [1, 2, 3, 5]
SEQ_LEN = 10


def main():
    states = pd.read_parquet(ROOT / "data" / "processed" / "states_w5s.parquet")
    with open(ROOT / "data" / "processed" / "scenario_split.txt") as f:
        lines = f.read().splitlines()
    test_ids = lines[1].split(":", 1)[1].split(",")

    bundle = joblib.load(ROOT / "artifacts" / "world_model" / "scaler.joblib")
    scaler, feature_columns = bundle["scaler"], bundle["feature_columns"]

    model = PrevailWorldModel(n_features=len(feature_columns))
    model.load_state_dict(torch.load(ROOT / "artifacts" / "world_model" / "world_model_v1.pt"))
    model.eval()

    max_K = max(K_VALUES)
    trajectories = build_trajectories(states, test_ids, feature_columns, SEQ_LEN, max_K)
    print(f"Built {trajectories['history'].shape[0]} rollout trajectories from {len(test_ids)} test scenarios")

    results = {}
    for K in K_VALUES:
        traj_K = {
            "history": trajectories["history"],
            "future_states": trajectories["future_states"][:, :K, :],
            "future_stage": trajectories["future_stage"][:, :K],
            "future_label": trajectories["future_label"][:, :K],
        }
        res = evaluate_k_step_error_accumulation(model, scaler, traj_K, K)
        results[f"K={K}"] = res
        print(f"K={K}:")
        for step in res["per_step"]:
            print(f"  t+{step['k']}: norm_mse={step['normalized_mse']:.3f} "
                  f"cos_sim={step['cosine_similarity']:.3f} stage_acc={step['stage_accuracy']:.3f} "
                  f"F1={step['f1']:.3f} FPR={step['false_positive_rate']:.3f} "
                  f"mean_P(attack)={step['mean_p_attack']:.3f}")

    out_dir = ROOT / "artifacts" / "rollout"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "k_step_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved -> {out_dir / 'k_step_results.json'}")


if __name__ == "__main__":
    main()
