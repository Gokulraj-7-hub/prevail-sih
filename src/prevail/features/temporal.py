"""Temporal / aggregate feature extraction (data-contract.md Sec 3.3).

These are the features that make a state genuinely *temporal* rather than a
per-window-independent snapshot: rates, deltas from S_{t-1}, and rolling
statistics over trailing history. Causal only -- never reads S_{t+1}.
"""
from __future__ import annotations

import numpy as np

from prevail.common.schema import TEMPORAL_FEATURES

ROLLING_WINDOW = 5


def compute_temporal_features(
    flow_feats: dict[str, float],
    prev_flow_feats: dict[str, float] | None,
    window_size_s: float,
    trailing_bytes_sum: list[float],
) -> dict[str, float]:
    flow_rate = flow_feats["total_connection_count"] / window_size_s
    packet_rate = flow_feats["packets_sum"] / window_size_s
    new_conn_rate = flow_feats["new_connection_count"] / window_size_s
    failed_conn_rate = flow_feats["failed_connection_count"] / window_size_s
    unique_dst_rate = flow_feats["unique_dst_ip_count"] / window_size_s

    burstiness = 0.0
    if flow_feats["iat_mean"] > 0:
        burstiness = flow_feats["iat_std"] / flow_feats["iat_mean"]

    delta_bytes = 0.0
    delta_packets = 0.0
    delta_new_conn = 0.0
    if prev_flow_feats is not None:
        delta_bytes = flow_feats["bytes_sum"] - prev_flow_feats["bytes_sum"]
        delta_packets = flow_feats["packets_sum"] - prev_flow_feats["packets_sum"]
        delta_new_conn = flow_feats["new_connection_count"] - prev_flow_feats["new_connection_count"]

    trailing = trailing_bytes_sum[-ROLLING_WINDOW:] if trailing_bytes_sum else []
    rolling_mean = float(np.mean(trailing)) if trailing else 0.0
    rolling_var = float(np.var(trailing)) if len(trailing) > 1 else 0.0

    feats = {
        "flow_rate": flow_rate,
        "packet_rate": packet_rate,
        "new_connection_rate": new_conn_rate,
        "failed_connection_rate": failed_conn_rate,
        "unique_destination_rate": unique_dst_rate,
        "port_entropy": flow_feats["dst_port_entropy"],
        "source_entropy": flow_feats["src_ip_entropy"],
        "burstiness": burstiness,
        "delta_bytes_sum": delta_bytes,
        "delta_packets_sum": delta_packets,
        "delta_new_connection_count": delta_new_conn,
        "rolling_mean_bytes_sum": rolling_mean,
        "rolling_var_bytes_sum": rolling_var,
    }
    assert set(feats.keys()) == set(TEMPORAL_FEATURES)
    return {k: (0.0 if not np.isfinite(v) else float(v)) for k, v in feats.items()}
