# PREVAIL — Source Requirements (SIH26153)

Date: 2026-09-20
Author: Research pass (automated, fork of lead engineering session)

## 0. Note on primary source

The master prompt (`PREVAIL_SIH26153_MASTER_PROMPT.md`) names `/mnt/data/bugbounty guide.pdf` as
the "primary source." **That file does not exist in this environment** (confirmed by direct
filesystem check — `ls /mnt/data` fails, no such directory). Per the master prompt's own rule
0.6 ("If the source material is ambiguous, record the ambiguity instead of inventing a
requirement"), this is logged in `open-questions.md` rather than silently substituted.

In its place, this document uses:

1. The official **SIH26153** problem statement, reconstructed from convergent secondary sources
   (see §1 below — not a direct PDF fetch, confidence noted per item).
2. The functional requirement list (FR-01…FR-17) already enumerated in the master prompt
   §1 and §6, which the team had already derived from the PS before this research pass.

## 1. Confirmed problem statement identity

**Not directly fetched from a literal SIH PDF** (the SIH 2026 master-catalogue PDF at
`sih-2026-problem-statements.shaikrohit187.workers.dev` returned raw PDF byte structure, not
extractable text, on fetch — see open-questions.md). Instead, PS 26153 was **cross-confirmed
independently across four unrelated public GitHub repositories**, each built by a different team
against the same PS, all agreeing on:

| Field | Value | Agreement |
|---|---|---|
| PS ID | 26153 | 4/4 repos |
| Organization | National Technical Research Organisation (NTRO) | 4/4 repos |
| Title (paraphrased consistently) | "AI based Network Attack Forecasting from Network Traffic Data" | 4/4 repos, near-identical wording |
| Theme | Blockchain & Cybersecurity | 2/4 repos explicitly stated |
| Category | Software | 3/4 repos explicitly stated |
| Core mandate | Learn network state transition dynamics `P(S_{t+1}\|S_t)` instead of independent-flow binary classification; forecast multi-stage infiltration; map to MITRE ATT&CK | 4/4 repos |

Sources (all fetched 2026-09-20):
- https://github.com/HowSuyash/AttackForecast
- https://github.com/syednzaheer/SIH-P.S.-26153-Defender
- https://github.com/abdulmuqeeth-ai/AI-Network-Attack-Forecasting
- https://github.com/Kshitiz-Khandelwal/AI-Based-Forecasting-SIH2026

**Confidence assessment:** High for ID/org/title/core-mandate (independent convergence across
teams that have no obvious reason to collude on paraphrasing). **Not verified** for the literal
PDF wording, exact non-functional constraints, exact deliverable list, or scoring rubric — those
require the literal PS PDF, which this research pass could not extract. Treat every requirement
below as "derived from convergent secondary evidence," not "quoted from the primary document."

This matters because it means the master prompt's FR-01…FR-17 list (§6 below) — which the human
team had already produced before this research pass — is being used as the **working
requirement set**, cross-checked against, not overridden by, this secondary PS reconstruction.
No conflict was found between the two (see §4).

## 2. Terminology (preserved, not redefined casually)

These definitions are binding for all PREVAIL code, docs, and reports. Do not use these terms
loosely or interchangeably with adjacent concepts.

- **Network state (`S_t`)** — A single structured snapshot of network behaviour aggregated over
  one temporal window `[t, t+Δ)`, expressed as a fixed-schema vector of flow-level,
  packet-level, and temporal/aggregate features (see `data-contract.md`). A state is a
  *summary*, not raw packets — it discards nothing systematically important but is not a 1:1
  replay of traffic.

- **Temporal state** — Synonym used when emphasizing that a `NetworkState` is one element of an
  ordered sequence `[S_0, S_1, ..., S_t]`, not an independent sample. The word "temporal"
  signals that order and recency carry information the model is allowed to use.

- **State transition** — The (unknown, learned) function/distribution `P(S_{t+1} | S_t, S_{t-1},
  ..., S_{t-n})` that the World Model approximates. A transition is a *prediction*, not an
  observed fact, until the corresponding real window arrives.

- **World Model** — The learned component that approximates state-transition dynamics and can be
  run forward without new observations ("in imagination") to produce `S_hat_{t+1}, S_hat_{t+2},
  ...`. A model that only classifies the *current* state (e.g., "state t is malicious/benign")
  is **not** a World Model under this definition, even if it uses a "temporal" architecture like
  an LSTM — it must be able to roll forward multiple steps without new ground-truth input.

- **K-step rollout** — The autoregressive process of feeding a World Model's own prediction back
  in as input to produce `S_hat_{t+1} -> S_hat_{t+2} -> ... -> S_hat_{t+K}`, for a specified
  integer `K`. Error accumulation across steps must be measured and reported, not assumed away.

- **Infiltration state** — A `NetworkState` (real or predicted) whose behavioural indicators are
  consistent with an attacker having achieved some level of unauthorized presence or progress in
  the network, as opposed to `benign`/`reconnaissance-only`. This is a *label category*, not a
  binary "attack/no attack" flag — it exists on a normalized attack-stage vocabulary
  (`configs/features/attack_stage_mapping.yaml`).

- **Attack trajectory** — An ordered sequence of (predicted or observed) attack stages over time,
  e.g. `Recon -> Discovery -> Initial Access -> Lateral Movement -> C2`. A trajectory is the
  *narrative* PREVAIL outputs; it is built from per-step stage probabilities, not asserted as
  certain fact.

- **Explainability** — Evidence, in the form of (a) feature attribution for a specific prediction
  and (b) identification of which historical windows contributed most, presented alongside every
  forecast. Explainability output must use the phrase "contributed to the model's prediction,"
  never "caused" or "proves."

- **Packet-level feature** — A feature computed from individual packet headers/metadata within a
  window (TTL, TCP window size, fragmentation flags, retransmission indicators, inter-packet
  timing, payload-size distribution). Requires raw packet access (PCAP or equivalent); absent
  when only flow/NetFlow-style records are available (must be explicitly flagged missing, not
  imputed as zero silently — see `data-contract.md`).

- **Flow-level feature** — A feature computed from an aggregated network flow record (5-tuple:
  src/dst IP, src/dst port, protocol) such as byte/packet counts, duration, TCP flag ratios,
  inter-arrival statistics. Available from NetFlow/IPFIX-style exports even without raw packets.

## 3. Requirement extraction table

Source column key: `PS` = SIH26153 (secondary-confirmed, §1), `MP` = master prompt (human-authored,
pre-existing FR list), `PS+MP` = both agree.

| Requirement | Mandatory? | Source | Implementation plan | Validation |
|---|---|---|---|---|
| Import flow/packet telemetry (dataset or PCAP) | Yes | PS+MP (FR-01) | `src/prevail/ingestion/` — CSV/NetFlow adapter first, PCAP adapter second | Unit test: known-good file loads to expected row count; malformed file raises typed error, not crash |
| Extract flow-level features | Yes | PS+MP (FR-02) | `src/prevail/features/flow.py`, spec in `data-contract.md` | Unit tests per feature; compare against hand-computed values on a fixed toy flow |
| Extract packet-level features where source permits | Yes, conditional on packet data availability | PS+MP (FR-03) | `src/prevail/features/packet.py`; `has_packet_features` boolean carried in state | Unit tests; integration test with flow-only input confirms graceful degradation |
| Construct temporal windows | Yes | PS+MP (FR-04) | `src/prevail/preprocessing/windowing.py`, configurable window size (5s default, sweep 5/10/30s) | Property test: window boundaries non-overlapping and monotonic |
| Construct `NetworkState` objects | Yes | PS+MP (FR-05) | `src/prevail/states/` per `data-contract.md` schema | Schema validation test (pydantic) |
| Construct chronological state sequences | Yes | PS+MP (FR-06) | `src/prevail/sequences/` | Property test: sequence order == timestamp order, no shuffling |
| Learn `P(S_{t+1}\|S_t)` — the World Model | **Yes — this is the PS's central, non-negotiable requirement** | PS (core mandate) + MP §1 | `src/prevail/world_model/` — start with small temporal Transformer per master prompt §13 | One-step prediction error must beat a naive persistence baseline (`S_hat_{t+1} = S_t`) before proceeding |
| K-step forward rollout | **Yes — explicitly named in PS core mandate** | PS + MP (FR-10) | `src/prevail/rollout/` | Property test: rollout of length K returns exactly K states; error-accumulation curve reported for K∈{1,2,3,5} |
| Future infiltration/attack probability | Yes | PS+MP (FR-11) | `src/prevail/attack_stage/` consuming rollout output | Calibration check (reliability diagram), not just "looks reasonable" |
| Attack-stage interpretation | Yes | PS+MP (FR-12) | Normalized stage vocabulary, `configs/features/attack_stage_mapping.yaml` | Manual review of mapping confidence + rationale fields |
| MITRE ATT&CK mapping | Yes | PS+MP (FR-13) | `src/prevail/attack_mapping/`, versioned mapping table | Mapping confidence must be recorded; no technique claimed without supporting evidence field |
| Explainability | Yes | PS+MP (FR-14) | `src/prevail/explainability/` — SHAP/feature attribution + temporal evidence | Output includes evidence list + contributing windows; language reviewed for causal-claim leakage |
| Logistic Regression baseline comparison | **Yes — explicitly named metric requirement** | PS+MP (FR-07, FR-15) | `src/prevail/baselines/logistic_regression.py` | Precision/Recall/F1/FPR reported side-by-side with World Model on identical splits |
| Precision / Recall / F1 / FPR reporting | Yes | PS+MP | `src/prevail/evaluation/` | Fixed-seed regression test with tolerance band |
| Offline / air-gapped operation | Yes | PS+MP (FR-16) | Docker packaging, no outbound calls at runtime | Explicit test: disable network, run forecast end-to-end |
| Reproducible evaluation | Yes | MP (non-functional) | Experiment manifest (git commit, dataset version, seed, config) per run | Manifest present and complete for every reported number |
| Defensive what-if intervention simulator | **No — explicitly framed as "Proposed innovation / extension beyond the mandatory PS requirement"** (per master prompt rule 0.5) | MP §5, §20 (not found stated as mandatory in any of the 4 secondary PS sources) | `src/prevail/intervention/`, built only after core forecasting works | Must never claim causal prevention; language constrained to "forecasts lower probability under simulated intervention" |

## 4. Conflicts between PS (secondary-confirmed) and master prompt's FR list

**None found.** The four independently-built SIH26153 repos inspected all implement a subset of
the same FR-01…FR-17 list already present in the master prompt, which is strong secondary
evidence the master prompt's FR list is an accurate PS extraction, not an invention. The one
item all four repos agree is *not* explicitly mandated by the PS itself — the what-if
intervention/counterfactual simulator — matches the master prompt's own framing of it as a
"proposed extension," so there is no conflict to flag, only confirmation.

One soft discrepancy worth tracking: two of the four repos (`HowSuyash/AttackForecast`,
`Kshitiz-Khandelwal/AI-Based-Forecasting-SIH2026`) interpret "attack stage" as a 5–7-stage kill
chain with slightly different stage names and orderings (e.g., one places Lateral Movement before
C2, another after). This confirms the master prompt's own instruction (§10) to *not* force a
single rigid taxonomy across datasets, and to keep dataset-native label → normalized behaviour →
ATT&CK tactic as three separate, explicitly-mapped layers rather than asserting one canonical
stage list.

## 5. What this means for PREVAIL's architecture

No architectural change to the master prompt's plan is required by this research pass. The
mandatory core (World Model, one-step, K-step, ATT&CK mapping, explainability, LR baseline,
offline operation) is confirmed as PS-mandatory by convergent independent evidence. The
what-if simulator remains correctly labeled as an extension. See `differentiation.md` for how
PREVAIL should position itself given that at least one existing public repo
(`HowSuyash/AttackForecast`) already implements a scientifically serious version of the
mandatory core.
