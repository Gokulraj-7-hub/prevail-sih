# PREVAIL — Network State Data Contract

Status: DRAFT v0.1

## 1. Terminology (preserved verbatim in meaning from the master prompt)

- **network state**: a single point-in-time (window-aggregated) snapshot of observable network behaviour, represented as a structured feature vector (`NetworkState`).
- **temporal state**: a `NetworkState` considered as one element of an ordered sequence — i.e. a state with a defined position in time relative to its neighbours.
- **state transition**: the (unknown, learned) function mapping `S_t → S_{t+1}` that the World Model approximates.
- **World Model**: the learned model of state-transition dynamics — distinguished from a classifier by the fact that its primary output is a *predicted future state* (or distribution over states), not a single current-instant label.
- **K-step rollout**: repeated autoregressive application of the World Model, feeding each predicted state back in as input, to produce `Ŝ_{t+1}...Ŝ_{t+K}`.
- **infiltration state**: a `NetworkState` (real or predicted) whose behavioural indicators are consistent with an active attack-stage other than benign/idle.
- **attack trajectory**: the ordered sequence of attack-stage labels (real or predicted) associated with a sequence of states, e.g. `Recon → Discovery → Initial Access → Lateral Movement`.
- **explainability**: evidence (feature attribution + temporal window attribution) presented to justify a specific model output, explicitly not a causal claim.
- **packet-level feature**: a feature computed from individual packets within a window (requires raw packet access).
- **flow-level feature**: a feature computed from an aggregated flow record (5-tuple + statistics) within a window.

## 2. NetworkState schema

```text
NetworkState
    timestamp            # window end time, UTC epoch seconds
    window_start
    window_end
    window_size_s         # experimental hyperparameter, default 5
    scenario_id            # which capture/session this window belongs to (for leakage-safe splitting)
    flow_features           # dict, see §3
    packet_features          # dict, see §3 (nullable if source has no packet-level data)
    temporal_features         # dict, see §3
    metadata                    # dict: source dataset, capture id, feature-schema version
    attack_label              # TRAINING/EVAL ONLY — never fed into the predictive feature vector
    attack_stage             # TRAINING/EVAL ONLY — never fed into the predictive feature vector
```

**Leakage rule (hard constraint):** `attack_label` and `attack_stage` are stored on the `NetworkState` object for supervision/evaluation only. The feature-vector assembly step (`src/prevail/features/`) must never read these fields when building the model input tensor. Enforced by a property test (`tests/property/test_no_label_leakage.py`).

## 3. Feature registry

Every feature must be registered in `configs/features/feature_registry.yaml` with: `name, type, unit, source, calculation, missing_value_strategy, leakage_risk, justification`.

### 3.1 Flow-level (FR-02)

| Feature | Type | Notes |
|---|---|---|
| src/dst IP statistics (unique count, entropy) | float | aggregated per window, IP itself never used directly as a feature (avoid overfitting to specific hosts / dataset artifacts) |
| src/dst port statistics (unique count, entropy, well-known ratio) | float | |
| protocol distribution (TCP/UDP/ICMP/other ratio) | float[4] | |
| TCP flag ratios (SYN, ACK, FIN, RST, PSH, URG) | float[6] | |
| bytes (sum, mean, std per flow in window) | float | |
| packets (sum, mean, std per flow in window) | float | |
| flow duration (mean, std) | float | |
| inter-arrival time (mean, std) | float | |
| bidirectional traffic ratio | float | fwd_bytes / (fwd_bytes+bwd_bytes) |
| connection counts (new, total) | int | |
| failed connection counts (SYN w/o ACK, RST) | int | |

### 3.2 Packet-level (FR-03, nullable)

| Feature | Type | Notes |
|---|---|---|
| TTL (mean, std, distinct values) | float | |
| TCP window size (mean, std) | float | |
| fragmentation ratio | float | |
| payload-size distribution (mean, std, percentiles) | float | |
| retransmission count/ratio | float | requires sequence-number tracking |
| packet timing (IAT mean/std at packet granularity) | float | |
| port-access sequence characteristics (scan-like ordering score) | float | heuristic, documented separately |

### 3.3 Temporal / aggregate (computed over window + rolling history)

| Feature | Type | Notes |
|---|---|---|
| flow rate, packet rate | float | per second |
| new-connection rate, failed-connection rate | float | |
| unique-destination rate | float | |
| port entropy, source entropy | float | Shannon entropy over the window |
| traffic burstiness | float | coefficient of variation of inter-arrival times |
| change from previous window (delta features) | float | requires ordered access to `S_{t-1}` only — never `S_{t+1}` |
| rolling mean / rolling variance | float | fixed-size trailing window, configurable |

**Feature count discipline:** target a curated set (aim: <100 features v1) rather than blind expansion — every addition must clear the registry's justification field.

## 4. Windowing (Phase 6)

Default: **5-second windows**, treated as an experimental hyperparameter. Also evaluate 10s and 30s (dataset-dependent) — see `docs/experiments/*`. Sequences: `[S0..S9] → S10` (sequence length also experimental, default 10).

**Leakage rule:** windows are built per `scenario_id`; sequences never cross scenario boundaries; train/test split is scenario- and/or time-aware, never a random shuffle of adjacent windows (see master prompt §2.4, §35).

## 5. Implementation notes (v1, recorded as decisions were made — see DECISIONS.md)

- **Flow definition scope**: v1 defines a "flow" as the set of packets sharing a 5-tuple (`src_ip, dst_ip, src_port, dst_port, protocol`) *within a single window*. Flows are not tracked continuously across window boundaries in v1 — a long-lived connection spanning multiple windows is treated as multiple flow instances, one per window. This is a documented simplification, not a leakage risk (each window's flow stats only use packets from that window). Revisit if evaluation shows this materially hurts long-flow attack stages (e.g. sustained C2 sessions).
- **`packet_features` nullability**: populated whenever the source data includes packet-level fields (true for the synthetic generator and for real PCAP ingestion); left `null` only for pure flow-record sources (e.g. a flow-CSV-only dataset with no packet access), per FR-03.
- **Attack-stage ground truth**: for the synthetic dataset (see DECISIONS.md D-003), each packet carries a simulator-assigned `attack_stage`. A window's `attack_stage` label is **presence-based, not majority-vote** (see DECISIONS.md D-005): a non-benign stage is assigned if it has at least a small minimum packet count in the window, regardless of whether benign background traffic numerically dominates that window. Majority-vote was tried first and rejected because it systematically mislabeled sparse-signal stages (initial-access exploit attempts, C2 beacons) as benign.

## 6. Open items

Tracked in `docs/research/open-questions.md`, including: concrete source dataset(s) to populate this contract against, and confirmation that the official SIH26153 PS does not mandate a different mandatory feature set.
