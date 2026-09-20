"""Packet-level feature extraction (data-contract.md Sec 3.2). Requires raw
packet fields; returns None (not zeros) when the source has none, per FR-03's
"where source data permits"."""
from __future__ import annotations

import numpy as np
import pandas as pd

from prevail.common.schema import PACKET_FEATURES

PORT_SCAN_MIN_UNIQUE_DPORTS = 5


def compute_packet_features(window_pkts: pd.DataFrame, has_packet_data: bool = True) -> dict[str, float] | None:
    if not has_packet_data:
        return None
    if len(window_pkts) == 0:
        return {name: 0.0 for name in PACKET_FEATURES}

    payload = window_pkts["payload_size"]
    pkt_iat = window_pkts.sort_values("timestamp")["timestamp"].diff().dropna()

    feats = {
        "ttl_mean": float(window_pkts["ttl"].mean()),
        "ttl_std": float(window_pkts["ttl"].std(ddof=0)) if len(window_pkts) > 1 else 0.0,
        "ttl_distinct_count": float(window_pkts["ttl"].nunique()),
        "tcp_window_mean": float(window_pkts["tcp_window"].mean()),
        "tcp_window_std": float(window_pkts["tcp_window"].std(ddof=0)) if len(window_pkts) > 1 else 0.0,
        "fragmentation_ratio": float(window_pkts["fragmented"].mean()),
        "payload_size_mean": float(payload.mean()),
        "payload_size_std": float(payload.std(ddof=0)) if len(payload) > 1 else 0.0,
        "payload_size_p95": float(payload.quantile(0.95)) if len(payload) else 0.0,
        "retransmission_ratio": float(window_pkts["retransmission"].mean()),
        "packet_iat_mean": float(pkt_iat.mean()) if len(pkt_iat) else 0.0,
        "packet_iat_std": float(pkt_iat.std(ddof=0)) if len(pkt_iat) > 1 else 0.0,
        "port_scan_score": _port_scan_score(window_pkts),
    }
    return {k: (0.0 if not np.isfinite(v) else v) for k, v in feats.items()}


def _port_scan_score(window_pkts: pd.DataFrame) -> float:
    """Heuristic: for the busiest single source IP in the window, the fraction
    of its packets that hit a *distinct* destination port -- close to 1.0 for
    a horizontal/vertical scan, low for normal repeat-connection traffic."""
    if len(window_pkts) == 0:
        return 0.0
    top_src = window_pkts["src_ip"].value_counts().idxmax()
    src_pkts = window_pkts[window_pkts["src_ip"] == top_src]
    if len(src_pkts) < PORT_SCAN_MIN_UNIQUE_DPORTS:
        return 0.0
    return float(src_pkts["dst_port"].nunique()) / float(len(src_pkts))
