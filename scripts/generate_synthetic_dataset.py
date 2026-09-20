#!/usr/bin/env python
"""Generate the synthetic validation dataset and write it to data/raw/.

See DECISIONS.md D-003 and src/prevail/ingestion/synthetic.py docstring for
why this exists and its limitations.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prevail.ingestion.synthetic import generate_dataset  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main():
    packets_df, meta_df = generate_dataset(
        n_attack_scenarios=25, n_benign_scenarios=15, seed=42, duration_s=300.0
    )
    out_dir = ROOT / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    packets_path = out_dir / "synthetic_packets.csv"
    packets_df.to_csv(packets_path, index=False)

    meta_dir = ROOT / "data" / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    meta_path = meta_dir / "scenarios.csv"
    meta_df.to_csv(meta_path, index=False)

    print(f"Wrote {len(packets_df):,} packet events across {meta_df.shape[0]} scenarios")
    print(f"  packets -> {packets_path}")
    print(f"  scenario metadata -> {meta_path}")
    print(meta_df["has_attack"].value_counts())


if __name__ == "__main__":
    main()
