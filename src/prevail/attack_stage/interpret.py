"""Builds the Phase 14 future-attack-probability output:

T+1 Recon             0.82
T+2 Discovery         0.74
...

by combining stage-probability predictions (real or rolled-out states) with
the ATT&CK mapping layer. Probabilities come from a model evaluated against
held-out data (see docs/experiments/attack-stage.md) -- never arbitrary
numbers (master prompt Phase 14: "do not display arbitrary confidence
numbers")."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from prevail.attack_mapping.mapper import AttackMapper
from prevail.attack_stage.model import predict_stage_probs
from prevail.common.schema import ATTACK_STAGES


def build_forecast_table(
    scaler: StandardScaler,
    clf: RandomForestClassifier,
    rolled_out_states: np.ndarray,  # (K, n_features), from rollout.k_step_rollout_batch for one trajectory
    mapper: AttackMapper,
) -> list[dict]:
    probs = predict_stage_probs(scaler, clf, rolled_out_states)  # (K, n_stages)
    table = []
    for k in range(probs.shape[0]):
        stage_idx = int(probs[k].argmax())
        stage = ATTACK_STAGES[stage_idx]
        entry = mapper.lookup(stage)
        table.append({
            "step": k + 1,
            "predicted_stage": stage,
            "stage_probability": float(probs[k, stage_idx]),
            "p_attack": float(1.0 - probs[k, ATTACK_STAGES.index("benign")]),
            "all_stage_probs": {ATTACK_STAGES[i]: float(probs[k, i]) for i in range(len(ATTACK_STAGES))},
            "attck_tactic": entry["tactic"],
            "attck_technique": entry["technique"],
            "attck_mapping_confidence": entry["confidence"],
        })
    return table
