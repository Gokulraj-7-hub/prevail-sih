"""Flow-level feature extraction (master prompt Phase 8, data-contract.md Sec 3.1).

A "flow" in v1 is the set of packets sharing a 5-tuple within a single window
(see data-contract.md Sec 5 implementation notes -- no cross-window flow
tracking yet).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from prevail.common.schema import FLOW_FEATURES
from prevail.features.entropy import shannon_entropy

FLOW_KEY = ["src_ip", "dst_ip", "src_port", "dst_port", "protocol"]


def compute_flow_features(window_pkts: pd.DataFrame) -> dict[str, float]:
    if len(window_pkts) == 0:
        return {name: 0.0 for name in FLOW_FEATURES}

    n_pkts = len(window_pkts)
    grouped = window_pkts.groupby(FLOW_KEY, sort=False)

    flow_bytes = grouped["payload_size"].sum()
    flow_pkt_counts = grouped.size()
    flow_duration = grouped["timestamp"].agg(lambda s: float(s.max() - s.min()))
    flow_has_syn = grouped["tcp_syn"].any()
    flow_has_ack = grouped["tcp_ack"].any()
    flow_has_rst = grouped["tcp_rst"].any()

    iat = window_pkts.sort_values("timestamp")["timestamp"].diff().dropna()

    proto_counts = window_pkts["protocol"].value_counts(normalize=True)

    feats = {
        "unique_src_ip_count": float(window_pkts["src_ip"].nunique()),
        "unique_dst_ip_count": float(window_pkts["dst_ip"].nunique()),
        "src_ip_entropy": shannon_entropy(window_pkts["src_ip"]),
        "dst_ip_entropy": shannon_entropy(window_pkts["dst_ip"]),
        "unique_src_port_count": float(window_pkts["src_port"].nunique()),
        "unique_dst_port_count": float(window_pkts["dst_port"].nunique()),
        "src_port_entropy": shannon_entropy(window_pkts["src_port"]),
        "dst_port_entropy": shannon_entropy(window_pkts["dst_port"]),
        "well_known_port_ratio": float((window_pkts["dst_port"] < 1024).mean()),
        "proto_tcp_ratio": float(proto_counts.get("TCP", 0.0)),
        "proto_udp_ratio": float(proto_counts.get("UDP", 0.0)),
        "proto_icmp_ratio": float(proto_counts.get("ICMP", 0.0)),
        "proto_other_ratio": float(proto_counts.get("OTHER", 0.0)),
        "tcp_syn_ratio": float(window_pkts["tcp_syn"].mean()),
        "tcp_ack_ratio": float(window_pkts["tcp_ack"].mean()),
        "tcp_fin_ratio": float(window_pkts["tcp_fin"].mean()),
        "tcp_rst_ratio": float(window_pkts["tcp_rst"].mean()),
        "tcp_psh_ratio": float(window_pkts["tcp_psh"].mean()),
        "tcp_urg_ratio": float(window_pkts["tcp_urg"].mean()),
        "bytes_sum": float(flow_bytes.sum()),
        "bytes_mean": float(flow_bytes.mean()) if len(flow_bytes) else 0.0,
        "bytes_std": float(flow_bytes.std(ddof=0)) if len(flow_bytes) > 1 else 0.0,
        "packets_sum": float(n_pkts),
        "packets_mean": float(flow_pkt_counts.mean()) if len(flow_pkt_counts) else 0.0,
        "packets_std": float(flow_pkt_counts.std(ddof=0)) if len(flow_pkt_counts) > 1 else 0.0,
        "flow_duration_mean": float(flow_duration.mean()) if len(flow_duration) else 0.0,
        "flow_duration_std": float(flow_duration.std(ddof=0)) if len(flow_duration) > 1 else 0.0,
        "iat_mean": float(iat.mean()) if len(iat) else 0.0,
        "iat_std": float(iat.std(ddof=0)) if len(iat) > 1 else 0.0,
        "bidirectional_ratio": _bidirectional_ratio(window_pkts),
        "new_connection_count": float((flow_has_syn & ~flow_has_ack).sum()),
        "total_connection_count": float(len(flow_pkt_counts)),
        "failed_connection_count": float((flow_has_syn & flow_has_rst).sum()),
    }
    return {k: (0.0 if not np.isfinite(v) else v) for k, v in feats.items()}


def _bidirectional_ratio(window_pkts: pd.DataFrame) -> float:
    """Fraction of 5-tuples (by unordered host pair) that see traffic in both directions."""
    pairs_fwd = set(zip(window_pkts["src_ip"], window_pkts["dst_ip"]))
    bidir = sum(1 for a, b in pairs_fwd if (b, a) in pairs_fwd)
    return float(bidir) / len(pairs_fwd) if pairs_fwd else 0.0
