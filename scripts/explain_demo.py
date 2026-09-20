#!/usr/bin/env python
"""Milestone 8: explainability demo on the same Case B trajectory used in
docs/experiments/attack-stage.md (T+1 forecast: initial_access)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import joblib  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402

from prevail.attack_stage.model import load_stage_model, predict_stage_probs  # noqa: E402
from prevail.common.schema import ATTACK_STAGES  # noqa: E402
from prevail.explainability.explain import build_explanation, format_explanation_text  # noqa: E402
from prevail.rollout.rollout import k_step_rollout_batch  # noqa: E402
from prevail.world_model.model import PrevailWorldModel  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SEQ_LEN = 10


def main():
    states = pd.read_parquet(ROOT / "data" / "processed" / "states_w5s.parquet")
    with open(ROOT / "data" / "processed" / "scenario_split.txt") as f:
        test_ids = f.read().splitlines()[1].split(":", 1)[1].split(",")

    bundle = joblib.load(ROOT / "artifacts" / "world_model" / "scaler.joblib")
    feature_columns = bundle["feature_columns"]

    demo_scenario = next(sid for sid in test_ids if "attack" in sid)
    sdf = states[states["scenario_id"] == demo_scenario].sort_values("window_id").reset_index(drop=True)
    first_attack_idx = int(sdf[sdf["attack_stage"] != "benign"].index.min())
    start_t = min(first_attack_idx, max(0, len(sdf) - SEQ_LEN))
    history = sdf.loc[start_t:start_t + SEQ_LEN - 1, feature_columns].to_numpy(dtype=float)

    wm_scaler = bundle["scaler"]
    model = PrevailWorldModel(n_features=len(feature_columns))
    model.load_state_dict(torch.load(ROOT / "artifacts" / "world_model" / "world_model_v1.pt"))
    model.eval()

    rollout_out = k_step_rollout_batch(model, wm_scaler, history[None, :, :], K=1)
    predicted_next_state = rollout_out["states"][0, 0]

    stage_scaler, stage_clf = load_stage_model(ROOT / "artifacts" / "attack_stage")
    probs = predict_stage_probs(stage_scaler, stage_clf, predicted_next_state[None, :])[0]
    predicted_class_idx = int(probs.argmax())
    predicted_stage = ATTACK_STAGES[predicted_class_idx]

    explanation = build_explanation(
        stage_scaler, stage_clf, feature_columns, predicted_next_state, predicted_class_idx,
        model, wm_scaler, history,
    )
    text = format_explanation_text(predicted_stage, explanation)
    print(text)

    out_dir = ROOT / "artifacts" / "explainability"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "demo_explanation.txt", "w") as f:
        f.write(text)
    print(f"\nSaved -> {out_dir / 'demo_explanation.txt'}")


if __name__ == "__main__":
    main()
