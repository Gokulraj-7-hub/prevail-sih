"""Combines feature attribution + temporal evidence into the master-prompt
Phase 19 output format."""
from __future__ import annotations

from prevail.explainability.shap_explain import explain_state
from prevail.explainability.temporal import temporal_window_importance


def build_explanation(scaler_stage, clf_stage, feature_columns, target_state, predicted_class_idx,
                       wm_model, wm_scaler, history) -> dict:
    feature_evidence = explain_state(scaler_stage, clf_stage, target_state, feature_columns, predicted_class_idx)
    temporal_evidence = temporal_window_importance(wm_model, wm_scaler, history)
    return {
        "feature_evidence": feature_evidence,
        "temporal_evidence": temporal_evidence,
        "disclaimer": (
            "Evidence shows what the model's prediction is sensitive to "
            "(feature attribution + input-window sensitivity). It is NOT a "
            "causal explanation of the underlying network activity."
        ),
    }


def format_explanation_text(predicted_stage: str, explanation: dict) -> str:
    lines = [f"Prediction: {predicted_stage}", "", "Important evidence:"]
    for i, ev in enumerate(explanation["feature_evidence"], start=1):
        lines.append(f"{i}. {ev['feature']} ({ev['direction']} confidence, shap={ev['shap_value']:.3f})")
    lines += ["", "Important windows:"]
    for w in explanation["temporal_evidence"][:5]:
        lines.append(f"{w['label']} (relative importance={w['importance_normalized']:.2f})")
    lines += ["", explanation["disclaimer"]]
    return "\n".join(lines)
