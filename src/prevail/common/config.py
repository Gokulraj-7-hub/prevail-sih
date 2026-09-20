"""Config loading and deterministic seeding, matching the reproducibility NFR in SRS.md."""
from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import yaml


def load_yaml(path: str | Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def set_global_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
    except ImportError:
        pass
