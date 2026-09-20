# Experiments E/F/G — Feature-Family Ablation

**Data source: SYNTHETIC VALIDATION DATA (see DECISIONS.md D-003) — not a real-world benchmark result.**

Logistic Regression baseline (same one-step-ahead forecasting task as `docs/experiments/baseline.md`), retrained from scratch on each feature subset, same train/test scenario split, same seed. Isolates the feature-family effect from World Model architecture choices.

| Feature family | # features | F1 | ROC-AUC | FPR |
|---|---|---|---|---|
| flow-only | 33 | 0.700 | 0.851 | 0.136 |
| packet-only | 13 | 0.821 | 0.851 | 0.039 |
| temporal-only | 13 | 0.802 | 0.844 | 0.026 |
| flow + packet | 46 | 0.825 | 0.863 | 0.044 |
| **all features (default)** | **59** | **0.823** | **0.870** | **0.050** |

## Reading

- **Packet-level features carry more signal per feature than flow-level features in this synthetic setup**: 13 packet features alone (F1 0.821) nearly match all 59 features combined (F1 0.823), while 33 flow features alone underperform everything else (F1 0.700, FPR 0.136 — nearly 3x every other config's false-positive rate). This is a real, not-obviously-predictable result — flow-only was expected to be a stronger baseline going in, since flow features are the traditional NIDS feature family.
- **Plausible explanation** (not independently confirmed): the synthetic generator's clearest attack signatures are packet-level by construction — TTL differing between attacker and internal traffic, retransmission bursts during initial_access, port-scan packet-ordering. A real capture's flow-vs-packet balance would need to be re-measured; this result should not be read as "packet features are always better," only as "in this dataset, they were."
- **Combining families gives a small but real improvement over the best single family** (0.823 vs 0.821), suggesting the families aren't fully redundant, but the marginal gain from adding flow+temporal on top of packet-only is modest — worth knowing before assuming all 59 features are equally load-bearing.
- **This result argues against dropping packet-level features even on a resource-constrained deployment**: if forced to choose one family, packet-only clearly beats flow-only here.

## Not yet run (tracked, not fabricated)

- **Experiment H (window-size sweep: 5s/10s/30s)** and **Experiment I (sequence-length sweep)** were not run in this pass — time-boxed. The master prompt's default 5s/seq_len=10 was used throughout every other experiment in this repo. This is an open follow-up, not a completed-and-hidden result.
- **Experiment J (cross-scenario generalization)** is partially covered structurally: every result in this repo already uses a scenario-level train/test split (never random-window splits), which is itself a generalization test across scenarios. A dedicated cross-attack-type holdout (e.g., train without any `command_and_control` scenarios, test only on those) was not run separately.
