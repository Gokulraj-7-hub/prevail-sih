"""Assemble NetworkState rows from windowed packets (architecture.md states/ module).

Produces one row per (scenario_id, window_id), including empty/idle windows
with zeroed features so that state sequences stay chronologically complete
(no missing timesteps for the sequence builder to silently paper over).
"""
from __future__ import annotations

import pandas as pd

from prevail.common.schema import ATTACK_STAGES, FLOW_FEATURES, PACKET_FEATURES
from prevail.features.flow import compute_flow_features
from prevail.features.packet import compute_packet_features
from prevail.features.temporal import compute_temporal_features
from prevail.features.windowing import DEFAULT_WINDOW_SIZE_S, assign_windows


MIN_ATTACK_PACKET_PRESENCE = 2


def _window_attack_stage(window_pkts: pd.DataFrame) -> str:
    """Presence-based labeling, NOT majority vote (see DECISIONS.md D-005): a
    window is labeled with a non-benign stage if that stage has at least
    MIN_ATTACK_PACKET_PRESENCE packets in the window, even if benign background
    traffic outnumbers it. Pure majority-vote systematically mislabeled sparse
    attack stages (initial_access exploit attempts, C2 beacons) as benign
    whenever they co-occurred with normal traffic -- which defeats the purpose
    of a forecasting system meant to catch exactly that low-and-slow signal."""
    if len(window_pkts) == 0 or "attack_stage" not in window_pkts.columns:
        return "benign"
    stages = window_pkts["attack_stage"].dropna()
    if len(stages) == 0:
        return "benign"
    counts = stages.value_counts()
    non_benign = counts.drop("benign", errors="ignore")
    non_benign = non_benign[non_benign >= MIN_ATTACK_PACKET_PRESENCE]
    if len(non_benign):
        return non_benign.idxmax()
    return "benign"


def build_states(
    packets: pd.DataFrame,
    window_size_s: float = DEFAULT_WINDOW_SIZE_S,
    has_packet_data: bool = True,
) -> pd.DataFrame:
    """Returns a flat DataFrame: one row per (scenario_id, window_id), with
    flow_*, packet_*, temporal_* columns (prefixed), attack_stage, attack_label.
    """
    windowed = assign_windows(packets, window_size_s)
    rows = []

    for scenario_id, sdf in windowed.groupby("scenario_id", sort=True):
        max_window = int(sdf["window_id"].max())
        scenario_start = float(sdf["window_start"].min())
        by_window = {wid: g for wid, g in sdf.groupby("window_id")}

        prev_flow_feats = None
        trailing_bytes: list[float] = []

        for wid in range(0, max_window + 1):
            wpkts = by_window.get(wid, sdf.iloc[0:0])
            flow_feats = compute_flow_features(wpkts)
            packet_feats = compute_packet_features(wpkts, has_packet_data=has_packet_data)
            temporal_feats = compute_temporal_features(
                flow_feats, prev_flow_feats, window_size_s, trailing_bytes
            )
            stage = _window_attack_stage(wpkts)

            row = {
                "scenario_id": scenario_id,
                "window_id": wid,
                "window_start": scenario_start + wid * window_size_s,
                "window_end": scenario_start + (wid + 1) * window_size_s,
                "timestamp": scenario_start + (wid + 1) * window_size_s,
                "window_size_s": window_size_s,
                "attack_stage": stage,
                "attack_label": int(stage != "benign"),
            }
            for k, v in flow_feats.items():
                row[f"flow__{k}"] = v
            if packet_feats is not None:
                for k, v in packet_feats.items():
                    row[f"packet__{k}"] = v
            else:
                for k in PACKET_FEATURES:
                    row[f"packet__{k}"] = None
            for k, v in temporal_feats.items():
                row[f"temporal__{k}"] = v
            rows.append(row)

            prev_flow_feats = flow_feats
            trailing_bytes.append(flow_feats["bytes_sum"])

    df = pd.DataFrame(rows)
    assert df["attack_stage"].isin(ATTACK_STAGES).all(), "unknown attack_stage produced"
    return df


def feature_columns(df: pd.DataFrame, families: tuple[str, ...] = ("flow", "packet", "temporal")) -> list[str]:
    return [c for c in df.columns if c.split("__")[0] in families]
