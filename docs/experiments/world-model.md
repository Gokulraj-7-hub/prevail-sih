# Experiment C — Temporal Transformer World Model V1, One-Step Prediction

**Data source: SYNTHETIC VALIDATION DATA (see DECISIONS.md D-003) — not a real-world benchmark result.**

- Architecture: 3-layer Transformer encoder, `d_model=64`, 4 heads, dropout 0.1, causal mask, Huber-loss state-regression head + auxiliary cross-entropy stage head (weight 0.3) — see `world_model/model.py` and D-007.
- Data: window 5s, seq_len 10, 59 features. Scenario-safe split: fit (24 scenarios) / val (6 scenarios, carved from the train split, never touching test) / test (10 scenarios, same held-out set the baseline uses).
- Training: AdamW, lr 1e-3, weight decay 1e-4, batch 32, early stopping patience 15 on val loss. Converged at epoch 26, best val loss 0.167.
- Artifacts: `artifacts/world_model/world_model_v1.pt`, `scaler.joblib`, `manifest.json`.

## One-step evaluation (test scenarios, Phase 12)

| Metric | Value | Reading |
|---|---|---|
| Overall normalized MSE | 0.369 | A "predict the training mean" baseline scores ~1.0 by construction of the normalization (D-008) — the model explains roughly 63% of held-out variance in next-window features. |
| Overall normalized MAE | 0.328 | |
| Mean cosine similarity (true vs. predicted next-state vector) | 0.714 | Directionally consistent, not a degenerate/collapsed prediction. |
| Auxiliary attack-stage accuracy | 0.940 | This is the joint aux head's own next-window stage classification, on the *same* window the state regression targets — a sanity signal, not the attack-probability pipeline (that's `attack_stage/`, downstream of predicted states, Milestone 7). |
| Trend correlation (predicted vs. true delta from current state) | 0.542 | Model tracks direction of change, not just magnitude — reasonable but not tight; see Limitations. |

Worst-predicted features by normalized MSE: `tcp_fin_ratio`, `delta_packets_sum`, `delta_new_connection_count`, `proto_icmp_ratio`, `burstiness` — all plausible "hard" features (sparse events / high natural variance), not an artifact of feature scale (fixed by D-008).

## Reading

One-step prediction is good enough to proceed to K-step rollout (Milestone 6) per master prompt Phase 12's gate ("if one-step prediction is poor, do NOT proceed to flashy K-step forecasting"). It is **not** a strong result in absolute terms — cosine similarity 0.71 and trend correlation 0.54 leave real room for improvement, expected at V1 with a 40-scenario synthetic dataset and no hyperparameter search yet (master prompt's own "starting points, not final values" framing, Sec 13).

## Limitations (carried into docs/limitations.md)

- Trained/evaluated on synthetic data only; absolute numbers do not transfer to real telemetry.
- No hyperparameter search performed yet (window size, seq length, d_model, layers all left at master-prompt defaults).
- Auxiliary stage accuracy (94%) is measured on the joint training objective's own head, not the downstream `attack_stage/` interpretation layer — do not conflate the two when reading later K-step/ATT&CK results.
