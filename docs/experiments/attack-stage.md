# Experiment — Attack-Stage Interpretation + ATT&CK Mapping (Phase 14, 17, 18)

**Data source: SYNTHETIC VALIDATION DATA (see DECISIONS.md D-003) — not a real-world benchmark result.**

Independent Random Forest classifier (`attack_stage/model.py`), trained on ground-truth states -> normalized attack_stage (all 1800 train-scenario windows, both benign and attack), architecturally separate from the World Model's own auxiliary head per `architecture.md`'s module boundary (this classifier is the one applied to both real states and rollout output).

![Attack stage per-class precision/recall](../../artifacts/charts/attack_stage_per_class.png)

## Classification report (600 held-out test-scenario states)

| Stage | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| benign | 0.970 | 1.000 | 0.985 | 481 |
| recon | 1.000 | 1.000 | 1.000 | 40 |
| initial_access | 1.000 | 0.688 | 0.815 | 16 |
| lateral_movement | 1.000 | 0.981 | 0.990 | 53 |
| command_and_control | 1.000 | 0.100 | 0.182 | 10 |

Overall accuracy: 0.975.

**Honest reading of the weak classes**: `command_and_control` recall (0.10, 10 test support) and `initial_access` recall (0.688, 16 support) are poor. This is a real limitation, not hidden: both are the rarest stages in the synthetic dataset (C2 beacons and exploit-attempt bursts are, by design, sparse relative to background traffic — see DECISIONS.md D-005), and 10-16 test examples is too few to trust the recall estimate itself, let alone expect strong recall. This needs more scenarios (or oversampling / class-weighting beyond what `balanced_subsample` already applies) before any claim about real C2/exploit detection performance.

## Demo forecast table (Phase 14 format)

Two rollouts from the same held-out attack scenario (`scn_009_attack`), both using World Model V1 + this classifier + `attack_mapping/mapper.py` — reported to show a genuine limitation alongside a genuine success, not just the flattering case.

### Case A — rollout started with zero attack precursor in history (harder, honestly a near-miss)

History = the 10 windows immediately *before* the scenario's first non-benign window. Result: all 5 forecast steps predicted `benign` with P(attack) ~0.00-0.01. **The model failed to anticipate an attack with no leading signal in its input window.** This is expected, not a bug: nothing in 50 seconds of pure background traffic distinguishes "attack starts in 5 seconds" from "attack never happens" — forecasting genuinely requires some precursor signal to work from. Documented here so this limitation isn't discovered for the first time by an SIH judge.

### Case B — rollout started once initial_access is already in progress (real precursor signal present)

| Step | Predicted stage | Stage prob. | P(attack) | ATT&CK tactic | Mapping confidence |
|---|---|---|---|---|---|
| T+1 | initial_access | 0.60 | 0.62 | Initial Access (TA0001) | low |
| T+2 | initial_access | 0.59 | 0.60 | Initial Access (TA0001) | low |
| T+3 | lateral_movement | 0.90 | 0.92 | Lateral Movement (TA0008) | medium |
| T+4 | lateral_movement | 0.99 | 1.00 | Lateral Movement (TA0008) | medium |
| T+5 | lateral_movement | 1.00 | 1.00 | Lateral Movement (TA0008) | medium |

This is the trajectory the demo script (`docs/demo/demo-script.md`) is built around: correctly forecasts the initial_access -> lateral_movement progression with rising P(attack), and correctly surfaces the ATT&CK tactic per step with an honestly-scoped confidence rating (never claiming technique-level certainty the synthetic evidence doesn't support — see `configs/features/attack_stage_mapping.yaml`).

## Reading

Case A vs. Case B together are the honest headline result: PREVAIL forecasts progression of an *already-detected* attack well, but — like any model, and consistent with the "no unsupported causal/predictive claims" principle — it cannot conjure a warning from a window with no attack signal in it at all. Any demo or report copy must reflect this distinction, not imply PREVAIL predicts attacks from nothing.
