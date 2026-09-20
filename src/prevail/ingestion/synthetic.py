"""Synthetic packet-event telemetry generator.

This is NOT a substitute for a real network capture dataset. It exists to let
every downstream pipeline stage (windowing -> features -> states -> sequences
-> baseline -> world model -> rollout -> evaluation) be built and validated
end-to-end per master-prompt Sec 2.2 ("build the simplest scientifically valid
version first"), while real-dataset integration is tracked in
docs/research/open-questions.md (see DECISIONS.md D-003).

Every result produced against this data must be labeled
"synthetic validation data" wherever it is reported.

Each scenario is an independent simulated capture session with:
  - continuous background benign traffic among a random set of internal hosts
  - optionally, one embedded attack timeline: recon -> initial_access ->
    lateral_movement -> command_and_control, at a random start offset

Ground-truth per-packet attack_stage is recorded for supervision/evaluation
only; feature extraction (prevail.features) never reads it.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

import pandas as pd

COMMON_PORTS = [80, 443, 53, 22, 25, 3389, 8080, 8443]
LATERAL_PORTS = [445, 3389, 22, 135, 139]
VULN_PORT = 8080
C2_PORT = 4444

PACKET_COLUMNS = [
    "timestamp", "scenario_id", "src_ip", "dst_ip", "src_port", "dst_port",
    "protocol", "tcp_syn", "tcp_ack", "tcp_fin", "tcp_rst", "tcp_psh", "tcp_urg",
    "ttl", "tcp_window", "fragmented", "payload_size", "retransmission", "attack_stage",
]


@dataclass
class ScenarioSpec:
    scenario_id: str
    duration_s: float
    has_attack: bool
    internal_hosts: list[str]
    external_hosts: list[str]
    attacker_ip: str | None = None
    c2_ip: str | None = None
    compromised_host: str | None = None
    victim_host: str | None = None
    stage_intervals: dict[str, tuple[float, float]] = field(default_factory=dict)


def _random_ip(rng: random.Random, prefix: str) -> str:
    return f"{prefix}.{rng.randint(0, 254)}.{rng.randint(1, 254)}"


def make_scenario_spec(scenario_id: str, seed: int, has_attack: bool, duration_s: float = 300.0) -> ScenarioSpec:
    rng = random.Random(seed)
    n_internal = rng.randint(4, 10)
    internal_hosts = [_random_ip(rng, "10.0") for _ in range(n_internal)]
    external_hosts = [_random_ip(rng, f"{rng.randint(20,200)}.{rng.randint(0,255)}") for _ in range(6)]

    spec = ScenarioSpec(
        scenario_id=scenario_id,
        duration_s=duration_s,
        has_attack=has_attack,
        internal_hosts=internal_hosts,
        external_hosts=external_hosts,
    )
    if not has_attack:
        return spec

    attacker_ip = _random_ip(rng, f"{rng.randint(1,19)}.{rng.randint(0,255)}")
    c2_ip = _random_ip(rng, f"{rng.randint(200,220)}.{rng.randint(0,255)}")
    victim_host = rng.choice(internal_hosts)
    compromised_host = victim_host  # becomes the pivot after initial_access

    recon_start = rng.uniform(20, duration_s * 0.25)
    recon_dur = rng.uniform(15, 35)
    ia_start = recon_start + recon_dur + rng.uniform(2, 8)
    ia_dur = rng.uniform(8, 20)
    lm_start = ia_start + ia_dur + rng.uniform(5, 15)
    lm_dur = rng.uniform(25, 50)
    c2_start = lm_start + rng.uniform(0, 10)
    c2_dur = max(20.0, duration_s - c2_start - 5)

    spec.attacker_ip = attacker_ip
    spec.c2_ip = c2_ip
    spec.victim_host = victim_host
    spec.compromised_host = compromised_host
    spec.stage_intervals = {
        "recon": (recon_start, recon_start + recon_dur),
        "initial_access": (ia_start, ia_start + ia_dur),
        "lateral_movement": (lm_start, lm_start + lm_dur),
        "command_and_control": (c2_start, c2_start + c2_dur),
    }
    return spec


def _pkt(t, scenario_id, src, dst, sport, dport, proto, stage, rng, **kw):
    row = dict(
        timestamp=t, scenario_id=scenario_id, src_ip=src, dst_ip=dst,
        src_port=sport, dst_port=dport, protocol=proto,
        tcp_syn=False, tcp_ack=False, tcp_fin=False, tcp_rst=False, tcp_psh=False, tcp_urg=False,
        ttl=64, tcp_window=64240, fragmented=False, payload_size=0, retransmission=False,
        attack_stage=stage,
    )
    row.update(kw)
    return row


def _gen_benign(spec: ScenarioSpec, rng: random.Random) -> list[dict]:
    pkts = []
    rate = rng.uniform(4, 10)  # packets/sec background
    t = 0.0
    while t < spec.duration_s:
        t += rng.expovariate(rate)
        if t >= spec.duration_s:
            break
        src = rng.choice(spec.internal_hosts)
        if rng.random() < 0.3:
            dst = rng.choice(spec.external_hosts)
        else:
            dst = rng.choice([h for h in spec.internal_hosts if h != src] or spec.internal_hosts)
        proto = "TCP" if rng.random() < 0.85 else ("UDP" if rng.random() < 0.9 else "ICMP")
        dport = rng.choice(COMMON_PORTS) if proto != "ICMP" else 0
        sport = rng.randint(1024, 65535)
        is_new = rng.random() < 0.15
        pkts.append(_pkt(
            t, spec.scenario_id, src, dst, sport, dport, proto, "benign", rng,
            tcp_syn=is_new and proto == "TCP",
            tcp_ack=(not is_new) and proto == "TCP",
            tcp_fin=rng.random() < 0.05 and proto == "TCP",
            ttl=rng.choice([64, 128, 255]),
            tcp_window=rng.randint(8192, 65535),
            payload_size=max(0, int(rng.gauss(400, 300))),
            retransmission=rng.random() < 0.02,
        ))
    return pkts


def _gen_recon(spec: ScenarioSpec, rng: random.Random, start: float, end: float) -> list[dict]:
    pkts = []
    t = start
    ports_scanned: set[int] = set()
    while t < end:
        t += rng.expovariate(30)  # fast scan
        if t >= end:
            break
        dport = rng.randint(1, 65000)
        ports_scanned.add(dport)
        pkts.append(_pkt(
            t, spec.scenario_id, spec.attacker_ip, spec.victim_host,
            rng.randint(1024, 65535), dport, "TCP", "recon", rng,
            tcp_syn=True, ttl=rng.choice([54, 55]), tcp_window=1024, payload_size=0,
        ))
        if rng.random() < 0.4:  # some ports respond RST (closed)
            t2 = t + rng.uniform(0.001, 0.02)
            pkts.append(_pkt(
                t2, spec.scenario_id, spec.victim_host, spec.attacker_ip,
                dport, rng.randint(1024, 65535), "TCP", "recon", rng,
                tcp_rst=True, tcp_ack=True, ttl=64, tcp_window=0, payload_size=0,
            ))
    return pkts


def _gen_initial_access(spec: ScenarioSpec, rng: random.Random, start: float, end: float) -> list[dict]:
    pkts = []
    t = start
    attempts = 0
    while t < end:
        t += rng.uniform(0.3, 1.5)
        if t >= end:
            break
        attempts += 1
        success = t > end - rng.uniform(1, 3)  # succeeds near the end of the window
        pkts.append(_pkt(
            t, spec.scenario_id, spec.attacker_ip, spec.victim_host,
            rng.randint(1024, 65535), VULN_PORT, "TCP", "initial_access", rng,
            tcp_syn=True, ttl=54, tcp_window=1024, payload_size=rng.randint(400, 1400),
            retransmission=not success,
        ))
        if success:
            t2 = t + rng.uniform(0.01, 0.05)
            pkts.append(_pkt(
                t2, spec.scenario_id, spec.victim_host, spec.attacker_ip,
                VULN_PORT, rng.randint(1024, 65535), "TCP", "initial_access", rng,
                tcp_syn=True, tcp_ack=True, ttl=64, tcp_window=8192, payload_size=0,
            ))
    return pkts


def _gen_lateral_movement(spec: ScenarioSpec, rng: random.Random, start: float, end: float) -> list[dict]:
    pkts = []
    t = start
    targets = [h for h in spec.internal_hosts if h != spec.compromised_host]
    while t < end:
        t += rng.expovariate(8)
        if t >= end:
            break
        dst = rng.choice(targets) if targets else spec.compromised_host
        dport = rng.choice(LATERAL_PORTS)
        pkts.append(_pkt(
            t, spec.scenario_id, spec.compromised_host, dst,
            rng.randint(1024, 65535), dport, "TCP", "lateral_movement", rng,
            tcp_syn=rng.random() < 0.5, tcp_ack=True, ttl=64, tcp_window=32768,
            payload_size=rng.randint(100, 3000),
        ))
    return pkts


def _gen_c2(spec: ScenarioSpec, rng: random.Random, start: float, end: float) -> list[dict]:
    pkts = []
    beacon_interval = rng.uniform(4, 9)
    t = start
    while t < end:
        jitter = rng.uniform(-0.3, 0.3)
        t += beacon_interval + jitter
        if t >= end:
            break
        pkts.append(_pkt(
            t, spec.scenario_id, spec.compromised_host, spec.c2_ip,
            rng.randint(40000, 41000), C2_PORT, "TCP", "command_and_control", rng,
            tcp_psh=True, tcp_ack=True, ttl=54, tcp_window=2048,
            payload_size=rng.randint(40, 120),
        ))
    return pkts


def generate_scenario(spec: ScenarioSpec, seed: int) -> pd.DataFrame:
    rng = random.Random(seed)
    pkts = _gen_benign(spec, rng)
    if spec.has_attack:
        for stage, (s, e) in spec.stage_intervals.items():
            gen_fn = {
                "recon": _gen_recon,
                "initial_access": _gen_initial_access,
                "lateral_movement": _gen_lateral_movement,
                "command_and_control": _gen_c2,
            }[stage]
            pkts.extend(gen_fn(spec, rng, s, min(e, spec.duration_s)))
    df = pd.DataFrame(pkts, columns=PACKET_COLUMNS)
    return df.sort_values("timestamp").reset_index(drop=True)


def generate_dataset(
    n_attack_scenarios: int = 25,
    n_benign_scenarios: int = 15,
    seed: int = 42,
    duration_s: float = 300.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (packets_df, scenario_metadata_df)."""
    rng = random.Random(seed)
    all_packets = []
    meta_rows = []
    scenario_idx = 0
    for kind, count in [("attack", n_attack_scenarios), ("benign", n_benign_scenarios)]:
        for _ in range(count):
            scenario_idx += 1
            sid = f"scn_{scenario_idx:03d}_{kind}"
            s_seed = rng.randint(0, 2**31 - 1)
            spec = make_scenario_spec(sid, s_seed, has_attack=(kind == "attack"), duration_s=duration_s)
            df = generate_scenario(spec, s_seed)
            all_packets.append(df)
            meta_rows.append({
                "scenario_id": sid,
                "has_attack": spec.has_attack,
                "duration_s": spec.duration_s,
                "n_internal_hosts": len(spec.internal_hosts),
                "stage_intervals": str(spec.stage_intervals),
                "seed": s_seed,
            })
    packets_df = pd.concat(all_packets, ignore_index=True)
    meta_df = pd.DataFrame(meta_rows)
    return packets_df, meta_df
