# Explainability (Phase 19)

**Data source: SYNTHETIC VALIDATION DATA — not a real-world benchmark result.**

Two independent methods, combined in `explainability/explain.py`:

- **Feature attribution**: SHAP `TreeExplainer` over the `attack_stage` Random Forest classifier (`explainability/shap_explain.py`), applied to the World-Model-predicted next state. Explains which input features pushed the stage prediction toward the predicted class.
- **Temporal evidence**: occlusion-based window importance (`explainability/temporal.py`) — each historical window in the input sequence is replaced with the sequence mean, one at a time, and the resulting change in the World Model's prediction is measured. Chosen over extracting raw Transformer attention weights because occlusion measures actual output sensitivity (what the model's prediction depends on) rather than attention weight, which is a well-documented weak proxy for importance.

## Demo output (same Case B trajectory as docs/experiments/attack-stage.md)

```
Prediction: initial_access

Important evidence:
1. flow__tcp_syn_ratio (increased confidence, shap=0.109)
2. temporal__new_connection_rate (decreased confidence, shap=-0.068)
3. flow__new_connection_count (decreased confidence, shap=-0.059)
4. packet__ttl_distinct_count (increased confidence, shap=0.051)
5. flow__tcp_psh_ratio (increased confidence, shap=0.049)

Important windows:
T-1 (relative importance=1.00)
T-9 (relative importance=0.04)
T-10 (relative importance=0.04)
T-3 (relative importance=0.03)
T-2 (relative importance=0.03)
```

## Reading

- **Feature evidence is behaviourally sensible**: `tcp_syn_ratio` rising and `ttl_distinct_count` rising are consistent with our synthetic `initial_access` generator (repeated connection attempts from one external source, TTL differing from internal-host traffic) — the explanation is not arbitrary or disconnected from the underlying signal.
- **T-1 (the most recent window) dominates temporal importance (1.00 vs. ~0.03-0.04 for all others)** — expected given the causal Transformer's architecture (the most recent token has the shortest, most direct path to the prediction), and a useful sanity check that the occlusion method is measuring something real rather than noise.
- Per master prompt Phase 19, both outputs are labeled as "contributed to the model prediction," never as a causal account of the attacker's actual behaviour.
