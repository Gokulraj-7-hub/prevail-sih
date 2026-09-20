# PREVAIL — Defensive What-If Intervention Model

Status: DRAFT v0.1. **Proposed innovation / extension beyond the mandatory PS requirement** (master prompt §5, §17, §20; FR-17). Confirmed by independent research (`docs/research/differentiation.md`) as the one clean, evidenced differentiation gap versus 4 inspected SIH26153 competitor implementations — none of them implement a defensive what-if/counterfactual simulator.

## Non-negotiable language rule

Every output of this module says **"the model forecasts a lower probability under the simulated intervention"** — never "the intervention prevents/stops/blocks the attack." No causal methodology or experimental evidence backs a causal claim (master prompt §2.5). This is a model-based counterfactual, not a causal effectiveness study.

## Architecture

```text
Current state (most recent window in history)
     |
     v
Baseline forecast (K-step rollout, unmodified)
     |
     v
Intervention selector (one of the 6 interventions below)
     |
     v
Modified simulated state -- packet-level filter applied to the CURRENT
window's raw packets, then re-extracted through the SAME feature pipeline
as every other state (never a hand-edited feature vector -- see DECISIONS.md
D-009). Only the current window changes; earlier history windows are left
as observed.
     |
     v
World Model (same trained checkpoint, no retraining/fine-tuning per intervention)
     |
     v
Counterfactual forecast (K-step rollout from the modified history)
```

Implementation: `intervention/interventions.py` (spec + packet filter per type), `intervention/simulator.py` (recompute-and-splice), reusing `rollout/rollout.py` unchanged for both the baseline and counterfactual rollouts.

## Why packet-level, not feature-level (D-009)

PREVAIL's feature registry deliberately excludes raw IP addresses as features (data-contract.md: avoids overfitting to specific hosts/dataset artifacts). That means there is no "block this IP" feature to zero out — an honest intervention has to act where IPs still exist: the raw packets. Editing an aggregate feature like `unique_dst_ip_count` by hand would not be a real simulation of the intervention's effect on the *other* 58 correlated features in the same window; recomputing through the real feature-extraction pipeline is.

## Interventions (Phase 20 required per-intervention spec)

### 1. Isolate host

- **Precondition**: `host_ip` is identifiable in the current window's traffic.
- **State modification**: drop every packet where `src_ip == host_ip` or `dst_ip == host_ip`.
- **Assumptions**: isolation is instantaneous and total.
- **Limitations**: does not model partial/delayed isolation or prior exfiltration; no effect if `host_ip` has no traffic in this window.
- **Affected features**: `unique_src_ip_count`, `unique_dst_ip_count`, `bytes_sum`, `packets_sum`, `flow_rate`.
- **Expected side effect**: large drop in this window's total traffic if `host_ip` was a major traffic source (e.g. mid-lateral-movement).

### 2. Block source

- **Precondition**: `src_ip` identified as the suspicious originator.
- **State modification**: drop every packet where `src_ip == src_ip`.
- **Assumptions**: the source cannot trivially spoof a different IP.
- **Limitations**: does not model IP spoofing/rotation.
- **Affected features**: `unique_src_ip_count`, `src_port_entropy`, `new_connection_count`.

### 3. Block destination port

- **Precondition**: `port` is the suspected exploited/abused service port.
- **State modification**: drop every packet where `dst_port == port`.
- **Assumptions**: the targeted service is not also reachable on an alternate port.
- **Limitations**: does not model the attacker pivoting to a different port.
- **Affected features**: `well_known_port_ratio`, `dst_port_entropy`, `new_connection_count`.

### 4. Remove communication edge

- **Precondition**: both hosts, and the fact they communicate, are flagged suspicious.
- **State modification**: drop packets where `{src_ip,dst_ip} == {ip_a, ip_b}` in either direction; other traffic from either host is untouched.
- **Assumptions**: more surgical than full isolation — the rest of each host's traffic is legitimate.
- **Limitations**: an alternate path between the same two hosts (different protocol/port not distinguished at this granularity) is not removed.
- **Affected features**: `bidirectional_ratio`, `unique_dst_ip_count`, `total_connection_count`.

### 5. Segment asset

- **Precondition**: `host_ip` is a high-value/suspicious asset being placed into a restricted segment with an `allowed_peers` set.
- **State modification**: drop packets touching `host_ip` unless the other endpoint is in `allowed_peers`.
- **Assumptions**: `allowed_peers` correctly enumerates legitimate business need.
- **Limitations**: a too-permissive `allowed_peers` understates the effect; an attacker already inside an allowed peer is unaffected.
- **Affected features**: `unique_dst_ip_count`, `dst_ip_entropy`, `flow_rate`.

### 6. Disable suspicious connection

- **Precondition**: a specific flow has been flagged (e.g. by explainability evidence for this state).
- **State modification**: drop packets matching `(src_ip, dst_ip, dst_port)` exactly.
- **Assumptions**: the attacker does not immediately re-establish the identical connection within this window.
- **Limitations**: narrowest scope — no effect on any other flow, even from the same attacker.
- **Affected features**: `total_connection_count`, `bytes_sum`.

## See also

`docs/experiments/intervention.md` for a worked example (baseline vs. counterfactual forecast on a held-out synthetic scenario).
