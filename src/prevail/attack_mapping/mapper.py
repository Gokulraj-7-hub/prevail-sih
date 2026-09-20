"""ATT&CK mapping lookup (FR-13). Loads the versioned, human-authored mapping
file -- never generates a mapping at runtime, LLM or otherwise."""
from __future__ import annotations

from pathlib import Path

from prevail.common.config import load_yaml

DEFAULT_MAPPING_PATH = Path(__file__).resolve().parents[3] / "configs" / "features" / "attack_stage_mapping.yaml"


class AttackMapper:
    def __init__(self, mapping_path: str | Path = DEFAULT_MAPPING_PATH):
        data = load_yaml(mapping_path)
        self.schema_version = data["schema_version"]
        self.attck_version_referenced = data["attck_version_referenced"]
        self.mappings = data["mappings"]

    def lookup(self, normalized_stage: str) -> dict:
        entry = self.mappings.get(normalized_stage)
        if entry is None:
            raise KeyError(f"No ATT&CK mapping entry for stage '{normalized_stage}'")
        return entry
