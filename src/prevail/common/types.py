"""Core typed objects. NetworkState is the contract from docs/architecture/data-contract.md."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from prevail.common.schema import FLOW_FEATURES, PACKET_FEATURES, TEMPORAL_FEATURES


class PacketEvent(BaseModel):
    """One simulated/observed packet. Ingestion's atomic unit."""

    timestamp: float
    scenario_id: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str  # "TCP" | "UDP" | "ICMP" | "OTHER"
    tcp_syn: bool = False
    tcp_ack: bool = False
    tcp_fin: bool = False
    tcp_rst: bool = False
    tcp_psh: bool = False
    tcp_urg: bool = False
    ttl: int = 64
    tcp_window: int = 0
    fragmented: bool = False
    payload_size: int = 0
    retransmission: bool = False
    # Ground truth, present only in labeled/synthetic data. Never read by
    # features/ when building the model input vector (see data-contract.md).
    attack_stage: Optional[str] = None


class NetworkState(BaseModel):
    """One window-aggregated network state. See data-contract.md for the full spec."""

    timestamp: float
    window_start: float
    window_end: float
    window_size_s: float
    scenario_id: str
    flow_features: dict[str, float] = Field(default_factory=dict)
    packet_features: Optional[dict[str, float]] = None
    temporal_features: dict[str, float] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    # Training/eval only - must never be read by the feature-assembly step.
    attack_label: Optional[int] = None
    attack_stage: Optional[str] = None

    def to_vector(self, feature_order: Optional[list[str]] = None) -> list[float]:
        """Flatten to a fixed-order numeric vector for model input. No labels included."""
        merged: dict[str, float] = {}
        merged.update(self.flow_features)
        merged.update(self.packet_features or {f: 0.0 for f in PACKET_FEATURES})
        merged.update(self.temporal_features)
        order = feature_order or (FLOW_FEATURES + PACKET_FEATURES + TEMPORAL_FEATURES)
        return [float(merged.get(name, 0.0)) for name in order]
