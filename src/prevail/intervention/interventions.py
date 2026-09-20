"""Defensive intervention transformations (Phase 20, FR-17 -- PREVAIL's
proposed extension, not a mandatory PS requirement).

Every intervention is a packet-level filter, applied to the raw packets of
the *current* window before that window's features are recomputed (see
DECISIONS.md D-009 for why this is packet-level rather than a hand-edited
feature vector). This keeps every simulated state honestly derivable through
the same feature-extraction code path used everywhere else.

Master prompt: "Only support interventions that can be represented honestly
in the state representation." Because PREVAIL's feature registry deliberately
excludes raw IPs (data-contract.md: "IP itself never used directly as a
feature", to avoid host-identity overfitting), an intervention cannot be
"applied" by editing a feature vector -- it has to be applied to the packets
that produced it, upstream of that same anonymizing feature extraction.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd


@dataclass
class InterventionSpec:
    name: str
    description: str
    precondition: str
    state_modification: str
    assumptions: list[str]
    limitations: list[str]
    affected_features: list[str]
    filter_fn: Callable[[pd.DataFrame], pd.DataFrame]


def isolate_host(host_ip: str) -> InterventionSpec:
    return InterventionSpec(
        name=f"isolate_host({host_ip})",
        description=f"Remove all traffic to/from {host_ip} from the current window.",
        precondition="host_ip is reachable/identifiable in the current capture.",
        state_modification="Drop every packet where src_ip == host_ip or dst_ip == host_ip.",
        assumptions=["Isolation is instantaneous and total (no packets leak through before enforcement)."],
        limitations=[
            "Does not model partial/delayed isolation, or an attacker already having "
            "exfiltrated data before isolation.",
            "If host_ip is not actually present in this window's traffic, this "
            "intervention has no effect on the simulated state (correctly -- "
            "nothing to isolate yet).",
        ],
        affected_features=["unique_src_ip_count", "unique_dst_ip_count", "bytes_sum", "packets_sum", "flow_rate"],
        filter_fn=lambda df: df[(df["src_ip"] != host_ip) & (df["dst_ip"] != host_ip)],
    )


def block_source(src_ip: str) -> InterventionSpec:
    return InterventionSpec(
        name=f"block_source({src_ip})",
        description=f"Drop all traffic originating from {src_ip} (e.g. firewall rule on the attacker's IP).",
        precondition="src_ip is identified as the suspicious originator.",
        state_modification="Drop every packet where src_ip == src_ip.",
        assumptions=["The source cannot trivially spoof a different IP to bypass the block."],
        limitations=["Does not model IP spoofing/rotation, which would defeat this specific intervention."],
        affected_features=["unique_src_ip_count", "src_port_entropy", "new_connection_count"],
        filter_fn=lambda df, src_ip=src_ip: df[df["src_ip"] != src_ip],
    )


def block_destination_port(port: int) -> InterventionSpec:
    return InterventionSpec(
        name=f"block_destination_port({port})",
        description=f"Drop all traffic destined for port {port} (e.g. firewall rule on a specific service port).",
        precondition="port is the suspected exploited/abused service port.",
        state_modification="Drop every packet where dst_port == port.",
        assumptions=["The targeted service is not also reachable on an alternate port."],
        limitations=["Does not model the attacker pivoting to a different port for the same service."],
        affected_features=["well_known_port_ratio", "dst_port_entropy", "new_connection_count"],
        filter_fn=lambda df: df[df["dst_port"] != port],
    )


def remove_communication_edge(ip_a: str, ip_b: str) -> InterventionSpec:
    return InterventionSpec(
        name=f"remove_communication_edge({ip_a},{ip_b})",
        description=f"Drop all traffic between {ip_a} and {ip_b} specifically (both directions), leaving each host's other traffic untouched.",
        precondition="Both hosts, and the fact that they communicate, are identified as suspicious.",
        state_modification="Drop packets where {src_ip,dst_ip} == {ip_a, ip_b} in either direction.",
        assumptions=["More surgical than full host isolation -- other traffic from either host is legitimate."],
        limitations=["If the attacker has another path between the same two hosts (e.g. a different protocol/port pair not distinguished at this granularity), this intervention will not remove it."],
        affected_features=["bidirectional_ratio", "unique_dst_ip_count", "total_connection_count"],
        filter_fn=lambda df: df[~(((df["src_ip"] == ip_a) & (df["dst_ip"] == ip_b)) | ((df["src_ip"] == ip_b) & (df["dst_ip"] == ip_a)))],
    )


def segment_asset(host_ip: str, allowed_peers: set[str]) -> InterventionSpec:
    return InterventionSpec(
        name=f"segment_asset({host_ip})",
        description=f"Restrict {host_ip} to only communicate with a pre-approved peer set (network segmentation), dropping everything else.",
        precondition="host_ip is a high-value or suspicious asset being placed into a restricted segment.",
        state_modification="Drop packets where src_ip == host_ip or dst_ip == host_ip, unless the other endpoint is in allowed_peers.",
        assumptions=["allowed_peers correctly enumerates legitimate business-need communication."],
        limitations=["A too-permissive allowed_peers list understates the intervention's effect; an attacker already inside an allowed peer is unaffected."],
        affected_features=["unique_dst_ip_count", "dst_ip_entropy", "flow_rate"],
        filter_fn=lambda df: df[
            ((df["src_ip"] != host_ip) & (df["dst_ip"] != host_ip))
            | ((df["src_ip"] == host_ip) & (df["dst_ip"].isin(allowed_peers)))
            | ((df["dst_ip"] == host_ip) & (df["src_ip"].isin(allowed_peers)))
        ],
    )


def disable_suspicious_connection(src_ip: str, dst_ip: str, dst_port: int) -> InterventionSpec:
    return InterventionSpec(
        name=f"disable_suspicious_connection({src_ip}->{dst_ip}:{dst_port})",
        description="Drop one specific suspicious flow (5-tuple-level, minus src_port), e.g. killing a single active session.",
        precondition="The specific connection has been flagged (e.g. by the explainability evidence for this state).",
        state_modification="Drop packets matching (src_ip, dst_ip, dst_port) exactly.",
        assumptions=["The attacker does not immediately re-establish the same connection from the same source within this window."],
        limitations=["Narrowest-scope intervention -- does not generalize to any other flow, even from the same attacker."],
        affected_features=["total_connection_count", "bytes_sum"],
        filter_fn=lambda df: df[~((df["src_ip"] == src_ip) & (df["dst_ip"] == dst_ip) & (df["dst_port"] == dst_port))],
    )
