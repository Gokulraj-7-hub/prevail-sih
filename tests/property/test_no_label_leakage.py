"""Property: attack_label/attack_stage must never appear in the assembled
feature vector fed to a model (master prompt Phase 26 property tests)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pandas as pd

from prevail.states.builder import build_states, feature_columns
from prevail.ingestion.synthetic import generate_dataset


def test_feature_columns_exclude_labels():
    packets_df, _ = generate_dataset(n_attack_scenarios=2, n_benign_scenarios=1, seed=1, duration_s=30)
    states = build_states(packets_df, window_size_s=5.0)
    cols = feature_columns(states)
    assert "attack_label" not in cols
    assert "attack_stage" not in cols
    assert all("label" not in c.lower() for c in cols)
    assert all("stage" not in c.lower() for c in cols)


def test_to_vector_excludes_labels():
    from prevail.common.types import NetworkState

    state = NetworkState(
        timestamp=5.0, window_start=0.0, window_end=5.0, window_size_s=5.0,
        scenario_id="s", flow_features={"bytes_sum": 100.0},
        temporal_features={}, attack_label=1, attack_stage="recon",
    )
    vec = state.to_vector(feature_order=["bytes_sum"])
    assert vec == [100.0]
