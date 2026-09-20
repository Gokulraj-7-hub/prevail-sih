"""Feature attribution (Phase 19). SHAP TreeExplainer over the attack_stage
Random Forest -- explains WHY a given state (real or World-Model-predicted)
was interpreted as a particular stage. Never presented as causal (master
prompt: "do not equate feature attribution with causality"; language must be
'contributed to the model prediction')."""
from __future__ import annotations

import numpy as np
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


def explain_state(
    scaler: StandardScaler,
    clf: RandomForestClassifier,
    x: np.ndarray,  # (n_features,) raw units, one state
    feature_columns: list[str],
    predicted_class_idx: int,
    top_k: int = 5,
) -> list[dict]:
    x_scaled = scaler.transform(x.reshape(1, -1))
    explainer = shap.TreeExplainer(clf)
    sv = explainer.shap_values(x_scaled)
    # sklearn>=1.4 / shap versions can return (n_samples, n_features, n_classes)
    # or a list[n_classes] of (n_samples, n_features) -- normalize both to one array.
    if isinstance(sv, list):
        class_values = np.asarray(sv[predicted_class_idx])[0]
    else:
        sv = np.asarray(sv)
        class_values = sv[0, :, predicted_class_idx] if sv.ndim == 3 else sv[0]

    order = np.argsort(-np.abs(class_values))[:top_k]
    return [
        {
            "feature": feature_columns[i],
            "shap_value": float(class_values[i]),
            "direction": "increased" if class_values[i] > 0 else "decreased",
        }
        for i in order
    ]
