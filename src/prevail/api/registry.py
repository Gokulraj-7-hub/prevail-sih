"""Loads trained artifacts once at API startup. Models are ONLY ever loaded
from our own local artifacts/ directory, never from an upload path (threat-model.md:
"never load untrusted pickle files blindly")."""
from __future__ import annotations

from pathlib import Path

import joblib
import torch

from prevail.attack_mapping.mapper import AttackMapper
from prevail.world_model.model import PrevailWorldModel

ARTIFACTS_ROOT = Path(__file__).resolve().parents[3] / "artifacts"


class ModelRegistry:
    def __init__(self, artifacts_root: Path = ARTIFACTS_ROOT):
        self.artifacts_root = artifacts_root

        wm_bundle = joblib.load(artifacts_root / "world_model" / "scaler.joblib")
        self.feature_columns: list[str] = wm_bundle["feature_columns"]
        self.wm_scaler = wm_bundle["scaler"]

        self.world_model = PrevailWorldModel(n_features=len(self.feature_columns))
        self.world_model.load_state_dict(torch.load(artifacts_root / "world_model" / "world_model_v1.pt"))
        self.world_model.eval()

        stage_bundle = joblib.load(artifacts_root / "attack_stage" / "stage_classifier.joblib")
        self.stage_scaler = stage_bundle["scaler"]
        self.stage_clf = stage_bundle["model"]

        baseline_bundle = joblib.load(artifacts_root / "baseline" / "logistic_regression.joblib")
        self.baseline_scaler = baseline_bundle["scaler"]
        self.baseline_clf = baseline_bundle["model"]

        self.attack_mapper = AttackMapper()

    def experiment_dirs(self) -> list[str]:
        return sorted(
            p.name for p in self.artifacts_root.iterdir()
            if p.is_dir() and (p / "manifest.json").exists()
        )
