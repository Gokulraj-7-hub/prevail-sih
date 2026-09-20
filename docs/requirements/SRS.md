# PREVAIL — Software Requirements Specification (SRS)

Status: DRAFT v0.1 — derived directly from the SIH26153 master prompt (authoritative working spec while `docs/research/source-requirements.md` is being cross-checked against the official SIH26153 problem statement text). Any conflict discovered between the official PS and this SRS will be logged in `DECISIONS.md` and this file updated — nothing here is final until that cross-check lands.

## 1. Scope

PREVAIL is an offline-capable temporal network attack forecasting system. It is **not** a static IDS/classifier. Its core contract is a learned state-transition model (World Model) over temporal network state sequences, used to produce K-step forecasts of attack progression, mapped to MITRE ATT&CK, with explainability and an optional defensive what-if simulator.

## 2. Functional Requirements

| ID | Requirement | Notes |
|---|---|---|
| FR-01 | Import supported telemetry / datasets | PCAP and/or pre-extracted flow CSVs (e.g. CICFlowMeter-style). Untrusted-input handling required (see threat-model.md). |
| FR-02 | Extract flow-level features | See data-contract.md §Flow-level. |
| FR-03 | Extract packet-level features where source data permits | Only when raw packets are available; degrade gracefully to flow-only when not. |
| FR-04 | Construct temporal windows | Configurable window size, default 5s (see data-contract.md §Windowing). |
| FR-05 | Construct network states | `NetworkState` object per window — see data-contract.md. |
| FR-06 | Construct chronological state sequences | Ordered, non-overlapping-leak sequences per scenario/session. |
| FR-07 | Train Logistic Regression baseline | Required by PS. Must be reproducible (seed, config, coefficients saved). |
| FR-08 | Train World Model | Temporal Transformer encoder, V1 per architecture.md. |
| FR-09 | Predict next network state | One-step `S_t → Ŝ_{t+1}`. |
| FR-10 | Perform K-step forward rollout | Autoregressive rollout, K ∈ {1,2,3,5} tested. |
| FR-11 | Estimate future attack/infiltration probability | Derived from rolled-out states via attack-stage model. |
| FR-12 | Map forecast behaviour to attack stages | Normalized stage vocabulary, dataset-native → normalized → ATT&CK. |
| FR-13 | Map relevant behaviour to MITRE ATT&CK | Versioned mapping file with confidence + rationale. |
| FR-14 | Provide evidence-based explainability | Feature attribution (SHAP) + temporal evidence (contributing windows). |
| FR-15 | Evaluate against baseline | Precision/Recall/F1/FPR/ROC-AUC/PR-AUC, World Model vs Logistic Regression. |
| FR-16 | Provide offline operation | No cloud AI APIs, no internet calls at inference time. Docker-packaged. |
| FR-17 | Provide optional defensive what-if simulation | Labeled explicitly as proposed extension, not mandatory PS requirement. |

## 3. Non-Functional Requirements

- **Reproducibility**: every experiment records git commit, dataset version, feature version, model version, config, seed, metrics, timestamp (see MLOps/experiment manifest, architecture.md).
- **Offline capability**: full stack runs with network disabled after initial Docker build.
- **Deterministic preprocessing**: identical input → identical `NetworkState` sequence, no wall-clock or randomness leakage into features.
- **Model versioning**: models are content-addressed / semantically versioned artifacts, never silently overwritten.
- **Auditable experiments**: every run traceable to `docs/experiments/*` + `artifacts/`.
- **No hidden cloud dependency**: any optional LLM use (e.g., aiding ATT&CK-mapping authoring, not runtime inference) is outside the security-critical decision path and never required at inference time.
- **Reasonable inference latency**: single-state forecast should return interactively (target: sub-second on CPU for one-step, low-seconds for K=5 rollout) — to be measured, not assumed.
- **Clear failure states**: malformed/adversarial input produces a typed error, never a silent wrong prediction.
- **Safe handling of untrusted PCAPs**: parsing isolated, no arbitrary code execution, size/resource limits enforced (see threat-model.md).

## 4. Out of Scope (v1)

- Real-time in-line packet blocking / active response (PREVAIL forecasts and simulates; it does not enforce).
- Claims of causal intervention effectiveness (forecast-only language required, see master prompt §2.5).
- Multi-tenant SaaS deployment concerns.

## 5. Acceptance

This SRS is considered internally consistent once cross-checked against `docs/research/source-requirements.md`. Tracked in `DECISIONS.md`.
