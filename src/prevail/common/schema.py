"""Single source of truth for feature names, matching docs/architecture/data-contract.md.

Every module that builds or consumes a feature vector imports the ordered
lists here instead of hardcoding strings, so the feature registry YAML,
the model input tensor layout, and the docs stay in sync.
"""

FLOW_FEATURES = [
    "unique_src_ip_count",
    "unique_dst_ip_count",
    "src_ip_entropy",
    "dst_ip_entropy",
    "unique_src_port_count",
    "unique_dst_port_count",
    "src_port_entropy",
    "dst_port_entropy",
    "well_known_port_ratio",
    "proto_tcp_ratio",
    "proto_udp_ratio",
    "proto_icmp_ratio",
    "proto_other_ratio",
    "tcp_syn_ratio",
    "tcp_ack_ratio",
    "tcp_fin_ratio",
    "tcp_rst_ratio",
    "tcp_psh_ratio",
    "tcp_urg_ratio",
    "bytes_sum",
    "bytes_mean",
    "bytes_std",
    "packets_sum",
    "packets_mean",
    "packets_std",
    "flow_duration_mean",
    "flow_duration_std",
    "iat_mean",
    "iat_std",
    "bidirectional_ratio",
    "new_connection_count",
    "total_connection_count",
    "failed_connection_count",
]

PACKET_FEATURES = [
    "ttl_mean",
    "ttl_std",
    "ttl_distinct_count",
    "tcp_window_mean",
    "tcp_window_std",
    "fragmentation_ratio",
    "payload_size_mean",
    "payload_size_std",
    "payload_size_p95",
    "retransmission_ratio",
    "packet_iat_mean",
    "packet_iat_std",
    "port_scan_score",
]

TEMPORAL_FEATURES = [
    "flow_rate",
    "packet_rate",
    "new_connection_rate",
    "failed_connection_rate",
    "unique_destination_rate",
    "port_entropy",
    "source_entropy",
    "burstiness",
    "delta_bytes_sum",
    "delta_packets_sum",
    "delta_new_connection_count",
    "rolling_mean_bytes_sum",
    "rolling_var_bytes_sum",
]

ALL_FEATURES = FLOW_FEATURES + PACKET_FEATURES + TEMPORAL_FEATURES

# Normalized attack-stage vocabulary (dataset-native labels map onto this).
# Kept small and behaviourally grounded rather than exhaustively ATT&CK-shaped;
# see configs/features/attack_stage_mapping.yaml for the ATT&CK layer.
ATTACK_STAGES = [
    "benign",
    "recon",
    "initial_access",
    "lateral_movement",
    "command_and_control",
]
