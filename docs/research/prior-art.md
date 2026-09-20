# PREVAIL — Prior Art Research

Date: 2026-09-20

Scope: academic/open-source temporal attack-forecasting work, plus public SIH26153-specific
submissions found via web search. All rows below are backed by a real, fetched or search-indexed
URL — nothing in this table is fabricated. Where a claim could not be independently verified
(e.g., a repo's self-reported metrics), it is labeled "self-reported, not reproduced" rather than
presented as fact.

## SIH26153-specific implementations (direct competitors / closest reference set)

| Project | URL | Core approach | Features | Model | Forecasting? | K-step? | ATT&CK? | Explainability? | Intervention? | Gap vs PREVAIL |
|---|---|---|---|---|---|---|---|---|---|---|
| AttackForecast | https://github.com/HowSuyash/AttackForecast | RSSM (Recurrent State Space Model): encoder → latent → GRU dynamics, prior/posterior split so forecasting runs without future observations | 63 features (39 flow + 23 packet) on 60s windows, CTU-13 | RSSM w/ separate risk + anomaly channels | Yes, explicit "imagination mode" rollout | Yes | Yes, 5-stage kill chain derived from CTU-13 flow annotations + rules | Integrated gradients + causal attention weights + SHAP cross-check | **Not implemented** | Most scientifically mature prior art found. No what-if simulator — this is PREVAIL's clearest opening. Also: CTU-13-only, no cross-dataset generalization reported. |
| SIH-P.S.-26153-Defender | https://github.com/syednzaheer/SIH-P.S.-26153-Defender | 22-dim state vector → 2-layer PyTorch LSTM → autoregressive rollout | Flow-level, CSE-CIC-IDS2018 | LSTM, `P(S_{t+1}\|S_t)` | Yes | Yes, 1–10 steps | Yes, 5-stage | Perturbation-based sensitivity (zeroing features), not SHAP | **Explicitly stated as not implemented** | Honestly reports weak result: 72.5% FPR on cross-day (Wed→Thu) holdout despite 60.4% recall. Confirms cross-day generalization is genuinely hard — useful calibration for PREVAIL's own expectations. |
| AI-Network-Attack-Forecasting | https://github.com/abdulmuqeeth-ai/AI-Network-Attack-Forecasting | Rule/Markov-style stage-transition pipeline | Custom flow CSV, includes synthetic demo data | Markov-style transition probabilities | One-step only | **No** | Yes, technique-level (T1595, T1190, T1059) | Not implemented (future work) | Not implemented | Early-MVP maturity, no metrics reported. Confirms K-step + explainability + intervention are still open differentiators against the *median* public submission, even though the *best* one (AttackForecast) has closed the K-step/explainability gap. |
| AI-Based-Forecasting-SIH2026 | https://github.com/Kshitiz-Khandelwal/AI-Based-Forecasting-SIH2026 | 7-stage cascade (allowlist → threat feed → lexical ML → behavioral → geo-intel → World Model → active response); 2-layer GRU on 16-dim state | Multi-dataset claim: CIC-IDS-2017/2018, UNSW-NB15, CTU-13, CICIoT2023, DARPA | GRU, `P(S_{t+1}\|S_t)`, Markov transition-matrix rollout | Yes | Yes (+15m/+30m/+60m horizons) | Yes, 7-stage | TreeSHAP + temporal perturbation | **Not implemented** (states it emphasizes "preemptive containment," explicitly lacks counterfactual reasoning) | Reports suspiciously strong numbers (0 false positives across evaluation, 99.94% F1 on exfiltration stage) — **self-reported, not reproduced; treat with skepticism**, not as a bar PREVAIL must match. A 9-microservice production architecture for a hackathon submission is also atypical and worth treating cautiously as a completeness claim rather than a verified one. |
| Not fully inspected (found, not fetched) | https://github.com/MADOUT20/SIH-2026, https://github.com/Abhrxdip/attack_forecasting, https://github.com/Prasad14-cyber/network_attack_forecasting, https://github.com/chandanbodugam-max/CYBERWORLD--Network-Traffic-Analysis | Not verified | Not verified | Not verified | Not verified | Not verified | Not verified | Not verified | Listed by search as SIH 2026 network-forecasting-adjacent repos; not fetched in this pass (time-boxed). Recommend a follow-up pass inspects these before final differentiation claims are locked. |

## Academic / general prior art

| Project/Paper | URL | Core approach | Forecasting? | K-step? | ATT&CK? | Gap vs PREVAIL |
|---|---|---|---|---|---|---|
| Hybrid LSTM-Markov attack chain forecasting (SECRYPT 2026 submission) | https://github.com/mayank02raj/MITRE-ATTACK-based-Attack-Chain-Prediction | Trains on 4,849 campaign chains + 8,437 intrusion traces; constrained beam search generates 26,051 ranked multi-step futures | Yes | Yes (beam search over chain) | Yes, ATT&CK-native | 86% next-step accuracy, 0.76 Pearson vs NCISS severity (self-reported). Operates on **campaign/technique sequences**, not raw network telemetry state vectors — different input modality than PREVAIL (telemetry-grounded, not chain-corpus-grounded). No intervention simulator found in listing. |
| KillChainGraph | https://arxiv.org/pdf/2508.18230 | Phase-aware multi-model ensemble (ATTACK-BERT semantic phase mapping, LightGBM, custom Transformer, fine-tuned BERT, GNN) | Technique/phase classification, not multi-step telemetry rollout | Not applicable (not a rollout system) | Yes, phase-aware | 97.5–99.8% F1 across phases (self-reported). Strong ATT&CK-mapping reference architecture; not a World Model over network telemetry. |
| A Modular Framework for Rapidly Building Intrusion Predictors | https://arxiv.org/pdf/2511.23000 | General framework for intrusion *prediction* (pre-compromise), not just detection | Yes | Not confirmed | Not confirmed | Directly relevant framing ("predictors" vs "detectors") — worth a deeper read before Milestone 5. Not fetched in full in this pass. |
| Temporal Analysis Framework for Intrusion Detection Systems | https://arxiv.org/html/2511.03799v1 | Proposes taxonomy for time-aware IDS evaluation | N/A (taxonomy paper) | N/A | N/A | Useful for justifying PREVAIL's "no benchmark leakage" / time-aware split methodology (master prompt §2.4) with a citable taxonomy. |
| A Temporal Convolutional Network-based Approach for NIDS | https://arxiv.org/abs/2412.17452 | TCN with dilated convolutions, residual blocks | No (single-window classification) | No | No | Confirms TCN as a viable lighter-weight alternative to a Transformer for the World Model if the small-Transformer baseline (master prompt §13) underperforms; 96.7% accuracy on Edge-IIoTset (self-reported, different dataset than PREVAIL will use). |
| Temporal-Spatial Attention Network (TSAN) for DoS detection | https://arxiv.org/html/2503.16047v2 | Cross-attention over temporal + spatial (flow-graph) features | No | No | No | DoS-specific; confirms cross-attention as a plausible extension if flow-graph structure is added later — out of scope for V1. |
| SoK: The MITRE ATT&CK Framework in Research and Practice | https://arxiv.org/pdf/2304.07411 | Systematization-of-knowledge survey of how ATT&CK is (mis)used in research | N/A | N/A | N/A (survey of ATT&CK usage itself) | Important methodological check: this SoK is the right citation for justifying PREVAIL's conservative "confidence + rationale + review status" mapping fields (master prompt §10) rather than over-claiming technique-level precision. |

## Summary of what prior art already provides vs. what remains open

- **World Model / `P(S_{t+1}\|S_t)` forecasting**: already implemented, and implemented well, by
  at least one public SIH26153 team (`AttackForecast`). PREVAIL cannot claim this alone as
  differentiation — it is table stakes for a competitive submission, not a novel contribution.
- **K-step rollout**: implemented by 3 of 4 SIH26153 repos inspected. Also table stakes.
- **MITRE ATT&CK mapping**: implemented by all 4 SIH26153 repos inspected, at varying fidelity
  (technique-level in one, tactic/stage-level in the others). Table stakes.
- **Explainability**: implemented by 3 of 4 SIH26153 repos (SHAP/integrated-gradients in the
  strongest one, perturbation-based in another). Table stakes, though PREVAIL can differentiate
  on *rigor* (temporal evidence + feature attribution combined, with explicit non-causal
  language) rather than presence/absence.
- **What-if / counterfactual intervention simulator**: **not implemented in any of the 4
  SIH26153 repos inspected**, and one repo explicitly states it as a gap. This is the strongest,
  best-evidenced differentiation opportunity currently available to PREVAIL — see
  `differentiation.md`.
- **Cross-dataset / cross-scenario generalization**: only one repo (`Defender`) reports an
  honest cross-day evaluation, and it's weak (72.5% FPR). This is a real, evidenced open problem
  in the space, not a solved one — PREVAIL should budget real effort here rather than assume it
  will "just work," and should not promise better cross-day generalization without having
  actually measured it.
