# PREVAIL — Known Limitations

Consolidated from `docs/experiments/*.md` and `DECISIONS.md`. This file exists because master prompt §31 requires it as a top-level doc, and because the SIH demo script (`docs/demo/demo-script.md`) must not claim anything contradicted here.

## Data

- **All results to date are on a synthetic validation dataset** (`prevail.ingestion.synthetic`, DECISIONS.md D-003), not a real-world network capture. No number in this repo should be quoted as evidence of real-world detection/forecasting performance. Real-dataset integration is the top tracked open item (`docs/research/open-questions.md` OQ-2).
- The synthetic dataset has only 40 scenarios; the rarest attack stages (`command_and_control`: 21 windows total, `initial_access`: ~83) have too little support to trust their recall estimates (see `docs/experiments/attack-stage.md`).
- The primary source document named by the original task prompt (`bugbounty guide.pdf`) was never available in this environment (OQ-1) — requirements were cross-checked against the master prompt text and independent research into the public SIH26153 problem statement instead, not against that specific file.

## Forecasting

- One-step prediction quality (cosine similarity 0.71, trend correlation 0.54) leaves real room for improvement — no hyperparameter search has been run yet (`docs/experiments/world-model.md`).
- K-step rollout error accumulates roughly 2x from t+1 to t+5 (normalized MSE 0.376 -> 0.769) and stage-forecast F1 drops from 0.877 to 0.711 over the same range (`docs/experiments/k-step.md`). K=5 forecasts should be shown with visibly lower confidence than K=1 in any UI, never presented as equally reliable.
- **Onset forecasting from purely-benign precursor history performs poorly** (`docs/experiments/attack-stage.md` Case A): when an attack starts with literally zero signal in the preceding history window, the model correctly has nothing to detect and forecasts benign. This is an expected property of forecasting (not a bug), but must not be misrepresented in a demo as "PREVAIL predicts attacks before they start" in the general case — it forecasts *progression* of attacks that have already left some trace in the input window.

## Explainability

- Feature attribution (SHAP) and temporal evidence (occlusion) show what the model's own prediction is sensitive to, not a causal account of attacker behaviour (master prompt §2.5, enforced by an explicit disclaimer on every explanation output).

## Defensive what-if simulator (the proposed extension)

- **The mechanical pipeline works** (packet-level filtering -> honest feature re-extraction -> OOD sanity check -> re-rollout), but **the first real test showed both tested interventions increasing forecast P(attack) instead of decreasing it** (`docs/experiments/intervention.md`, DECISIONS.md D-010). An out-of-distribution check ruled out "the input is simply nonsense" as the explanation. The leading (unconfirmed) hypothesis is that the training data contains zero examples of a post-intervention window, so neither model has ever been taught what a successfully-defended state looks like.
- **Do not demo or claim that PREVAIL's what-if simulator currently shows interventions reducing predicted risk** — the evidence in hand says otherwise for the two interventions tested so far. The differentiator being demoed to SIH judges should be honestly framed as "PREVAIL can simulate and forecast the effect of a defensive action, and its current V1 models show measurably that they have NOT yet learned to expect a reduction from these specific interventions" — itself a legitimate, evidence-backed research finding, not a shipped capability claim.
- Recommended follow-up: augment training data with paired before/after-intervention synthetic scenarios so both models have some grounding for post-intervention traffic, then re-run `docs/experiments/intervention.md` as a regression check.

## Product / offline / security

- Offline packaging (Docker), the FastAPI backend, and the frontend dashboard are not yet built as of this pass (see `README.md` progress tracker) — everything above ran via `scripts/*.py`, not through the eventual product surface.
- Threat-model mitigations (`docs/architecture/threat-model.md`) are mostly "planned," not yet implemented/verified against a real API surface.

## General

- No hyperparameter search, ablation study (flow-only vs. packet-only vs. combined; window-size sweep; sequence-length sweep), or cross-dataset generalization test has been run yet (master prompt Experiments E-J). Everything reported here is a single configuration's first honest result, not a tuned or selected-best result.
