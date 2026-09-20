#!/usr/bin/env python
"""Milestone 3 pipeline: raw telemetry -> states -> scenario-safe sequences -> leakage
checks -> data quality report. Run after scripts/generate_synthetic_dataset.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from prevail.evaluation.data_quality import build_data_quality_report  # noqa: E402
from prevail.preprocessing.clean import clean_packets, load_packets  # noqa: E402
from prevail.sequences.builder import build_sequences  # noqa: E402
from prevail.sequences.split import scenario_train_test_split  # noqa: E402
from prevail.states.builder import build_states  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WINDOW_SIZE_S = 5.0
SEQ_LEN = 10


def main():
    raw_path = ROOT / "data" / "raw" / "synthetic_packets.csv"
    meta_path = ROOT / "data" / "metadata" / "scenarios.csv"
    if not raw_path.exists():
        raise SystemExit("Run scripts/generate_synthetic_dataset.py first")

    print("Loading + cleaning packets...")
    raw = load_packets(str(raw_path))
    packets, clean_report = clean_packets(raw)
    print(f"  {clean_report.as_dict()}")

    print(f"Building states (window={WINDOW_SIZE_S}s)...")
    states = build_states(packets, window_size_s=WINDOW_SIZE_S)
    print(f"  {len(states):,} states across {states['scenario_id'].nunique()} scenarios")

    processed_dir = ROOT / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    states.to_parquet(processed_dir / f"states_w{int(WINDOW_SIZE_S)}s.parquet", index=False)

    scenario_meta = pd.read_csv(meta_path)
    train_ids, test_ids = scenario_train_test_split(scenario_meta, test_fraction=0.25, seed=42)
    print(f"Scenario split: {len(train_ids)} train / {len(test_ids)} test")

    print(f"Building sequences (seq_len={SEQ_LEN})...")
    train_states = states[states["scenario_id"].isin(train_ids)]
    test_states = states[states["scenario_id"].isin(test_ids)]
    train_seq = build_sequences(train_states, seq_len=SEQ_LEN)
    test_seq = build_sequences(test_states, seq_len=SEQ_LEN)
    print(f"  train sequences: {train_seq['X'].shape}, test sequences: {test_seq['X'].shape}")

    np.savez_compressed(
        processed_dir / f"sequences_w{int(WINDOW_SIZE_S)}s_L{SEQ_LEN}_train.npz",
        X=train_seq["X"], y=train_seq["y"], y_stage=train_seq["y_stage"],
        y_label=train_seq["y_label"], scenario_id=train_seq["scenario_id"],
        target_window_id=train_seq["target_window_id"],
        feature_columns=np.array(train_seq["feature_columns"], dtype=object),
    )
    np.savez_compressed(
        processed_dir / f"sequences_w{int(WINDOW_SIZE_S)}s_L{SEQ_LEN}_test.npz",
        X=test_seq["X"], y=test_seq["y"], y_stage=test_seq["y_stage"],
        y_label=test_seq["y_label"], scenario_id=test_seq["scenario_id"],
        target_window_id=test_seq["target_window_id"],
        feature_columns=np.array(test_seq["feature_columns"], dtype=object),
    )

    with open(processed_dir / "scenario_split.txt", "w") as f:
        f.write("train:" + ",".join(train_ids) + "\n")
        f.write("test:" + ",".join(test_ids) + "\n")

    print("Building data quality report...")
    build_data_quality_report(
        packets, clean_report, states, scenario_meta, train_ids, test_ids,
        ROOT / "artifacts" / "data_quality_report.html",
    )
    print(f"  -> artifacts/data_quality_report.html")
    print("Pipeline complete.")


if __name__ == "__main__":
    main()
