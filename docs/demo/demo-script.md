# PREVAIL — SIH Demo Script (~2 minutes)

Every number below is from an actual run in this repo (`docs/experiments/*.md`), not scripted fiction. **State up front, once, briefly: "figures shown are on a synthetic validation dataset while real-dataset integration is in progress"** — then don't repeat the caveat every sentence; it's on-screen in the dashboard banner throughout.

Setup: `docker compose up --build`, dashboard at `localhost:3000`, dataset `demo`, scenario `scn_009_attack`, history end window `21`, K=5.

## 1. Load telemetry / show current state (15s)

Dashboard tab. "This is PREVAIL, an offline network attack forecasting system for SIH26153. We're looking at a captured session — 60 windows of network telemetry, 5 seconds each."

## 2. PREVAIL detects a trajectory (25s)

Switch to **Attack Trajectory** tab. "From the last 10 observed windows, PREVAIL's World Model — a small temporal Transformer, not a per-flow classifier — forecasts what happens next." Point at the chain: `initial_access (62%) → initial_access (60%) → lateral_movement (92%) → lateral_movement (100%) → lateral_movement (100%)`.

"Note the confidence: T+1 is more trustworthy than T+5 — error accumulates over the rollout, and the dashboard says so."

## 3. Click "Why?" (25s)

Switch to **Explainability** tab. "PREVAIL doesn't just output a number — it shows evidence. `tcp_syn_ratio` and `new_connection_rate` are driving this prediction, and the model is most sensitive to the most recent window, T-1 — which is exactly what you'd expect from a causal sequence model, a useful sanity check that this isn't noise." Point out the disclaimer: *not a causal explanation, evidence of model sensitivity.*

## 4. MITRE ATT&CK mapping (15s)

Switch to **MITRE Mapping** tab (or point at the Forecast Timeline's tactic column). "Every stage maps to a versioned, hand-authored ATT&CK tactic — Initial Access TA0001, Lateral Movement TA0008 — with an explicit confidence rating. We don't let a model invent ATT&CK techniques; low-confidence technique-level mappings are labeled low-confidence, not hidden."

## 5. What-if simulator (30s) — the honest part

Switch to **What-If Simulator** tab. "This is PREVAIL's proposed extension beyond the mandatory requirement — nobody else we found in our prior-art research implements this. You select a defensive action — say, block destination port 8080, the exploited port — and PREVAIL re-forecasts under that simulated change."

Run it live. **Show the real number, including the surprising one**: "In this run, the model actually forecasts a *higher* probability of continued attack, not lower. We dug into why — it's not because the simulated state is broken or nonsensical, we built a sanity check for that — the real reason is the current models have never seen a successfully-defended window during training, so they don't yet know what one looks like. That's a genuine, characterized limitation, and it's in our docs, not hidden. We'd rather show you a real result than a flattering one."

(This single moment is worth more credibility with judges than a fake success — it demonstrates the team validates its own claims, which several inspected competitor projects with suspiciously perfect self-reported metrics visibly do not.)

## 6. Compare with Logistic Regression (15s)

Switch to **Evaluation** tab. "Required by the PS: baseline comparison. Logistic Regression gets F1 0.823 forecasting one step ahead; our World Model's one-step normalized error explains about 63% of held-out variance — better than guessing the mean, meaningfully, not spectacularly. We're honest that this is V1, no hyperparameter search yet."

## 7. Close (5s)

"PREVAIL: an offline temporal World Model that forecasts attack trajectories, with evidence, ATT&CK context, and a defensive what-if layer we've stress-tested rather than just shipped. Thank you."

## Things to never say in the live demo

- "PREVAIL predicts attacks before they happen" (unqualified) — Case A in `docs/experiments/attack-stage.md` shows it cannot forecast an attack with zero precursor signal; say "forecasts progression of attacks already showing some signal."
- "The intervention prevents/stops the attack" — say "the model forecasts a probability change," per every disclaimer in the product itself.
- Any specific metric without "on synthetic validation data."
- Comparing our numbers to a competitor's self-reported 0% FP rate as if it were a target to beat — `docs/research/prior-art.md` flags that figure as unverified, not a bar we failed to clear.
