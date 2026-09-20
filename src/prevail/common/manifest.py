"""Experiment manifest — every training/eval run records this, per SRS.md reproducibility NFR
and master prompt Phase 27 (git commit, dataset version, feature version, model version,
config, seed, hardware, metrics, timestamp)."""
from __future__ import annotations

import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown (not a git repo or no commits yet)"


def build_manifest(
    experiment_name: str,
    dataset_version: str,
    feature_version: str,
    model_version: str,
    config: dict,
    seed: int,
    metrics: dict,
    extra: dict | None = None,
) -> dict:
    return {
        "experiment_name": experiment_name,
        "git_commit": _git_commit(),
        "dataset_version": dataset_version,
        "feature_version": feature_version,
        "model_version": model_version,
        "config": config,
        "seed": seed,
        "hardware": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python": platform.python_version(),
        },
        "metrics": metrics,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "extra": extra or {},
    }


def save_manifest(manifest: dict, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)
