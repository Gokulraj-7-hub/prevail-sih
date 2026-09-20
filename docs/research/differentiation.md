# PREVAIL — Differentiation Strategy

Date: 2026-09-20

This document follows master prompt §5 and is grounded in the actual findings of
`prior-art.md` — not a strawman. It is written skeptically: the honest conclusion is that
PREVAIL's *mandatory core* is not novel (a public competitor already does it well), and
PREVAIL's *one* well-evidenced differentiator is narrower than the master prompt's aspirational
framing suggests.

## 1. What prior work already does (confirmed by direct inspection, not assumption)

- `AttackForecast` (https://github.com/HowSuyash/AttackForecast) already implements, to a
  credible standard: a genuine World Model (RSSM architecture) that runs forward without new
  observations, K-step rollout, 5-stage MITRE ATT&CK mapping, and dual-method explainability
  (integrated gradients + causal attention + SHAP cross-check). It reports honest limitations
  (stage-forecasting doesn't transfer across malware families; only 3 of 5 stages are learnable
  from CTU-13). This is a serious, working implementation of the PS's mandatory core.
- Two other repos (`SIH-P.S.-26153-Defender`, `AI-Based-Forecasting-SIH2026`) also implement
  World Model + K-step + ATT&CK mapping + explainability, at varying quality.
- Academic work (KillChainGraph, the LSTM-Markov chain-forecasting SECRYPT submission) shows
  multi-step ATT&CK-aware forecasting is an active, populated research area, not a gap PREVAIL
  is uniquely positioned to fill.

**Conclusion: PREVAIL must not claim novelty for the mandatory core.** Doing the mandatory core
well is necessary but not differentiating, per master prompt §2.3 ("existing systems are not
automatically a reason to reject the PS" — but they are a reason to be honest that doing the same
thing is not innovation).

## 2. What PREVAIL does differently (evidenced, not aspirational)

**The defensive what-if / counterfactual intervention simulator** (master prompt §20) is the one
concrete feature that:

1. Is explicitly framed by the PS/master prompt as an *extension*, not a mandatory requirement
   (confirmed in `source-requirements.md` §3, §4).
2. Was **not found implemented in any of the 4 SIH26153 repos inspected** — one (`Defender`)
   explicitly states it as absent, `AttackForecast` and `AI-Based-Forecasting-SIH2026` both
   describe containment/response concepts but not counterfactual re-forecasting, and
   `AI-Network-Attack-Forecasting` doesn't mention it at all.
3. Is architecturally coherent with a World Model specifically (a static classifier cannot
   produce a counterfactual forecast — it has no forward dynamics to re-run under a modified
   state). This makes it a genuine extension *of* the mandatory core, not a bolt-on UI feature.

This is PREVAIL's primary claim to differentiation, and it rests on evidence gathered in this
research pass, not assertion.

## 3. Implementation detail vs. actual architectural contribution

| Item | Classification | Reason |
|---|---|---|
| Next.js dashboard, SOC-style UI | **Implementation detail** | At least one competitor already has a comparable "enterprise SOC console." A nicer UI is not an architectural contribution. |
| Small Transformer vs GRU vs LSTM vs RSSM for the World Model | **Implementation detail** | All four are valid "learned state-transition dynamics" implementations; competitors already span this space. Choice should be justified by ablation evidence (master prompt §13, §22), not claimed as innovation. |
| SHAP / integrated-gradients explainability | **Implementation detail** | Already done, in a more advanced form (integrated gradients + causal attention), by `AttackForecast`. |
| MITRE ATT&CK stage mapping with confidence/rationale/review-status fields | **Implementation detail, but a defensible rigor choice** | Mapping itself is table stakes; the explicit confidence/rationale/review-status discipline (master prompt §10) is a documentation practice, not an architecture, though it is worth keeping because two competitors' stage taxonomies conflict with each other (see `source-requirements.md` §4), suggesting sloppy mapping is a common competitor weakness. |
| **What-if intervention simulator with explicit per-intervention transformation functions, preconditions, and honest non-causal framing** | **Architectural contribution** | Requires the World Model's forward-simulation capability as a dependency; not found elsewhere; the "explicit transformation function per intervention" discipline (master prompt §20) is what makes it defensible rather than a hand-wavy demo trick. |
| Honest cross-day / cross-scenario generalization reporting | **Potential contribution, contingent on results** | Only one competitor (`Defender`) reports this, and reports it as weak (72.5% FPR). If PREVAIL measures and reports this rigorously — good or bad — that rigor itself is worth something in an SIH evaluation context, but it is a *methodology* contribution, not a modeling one, and must not be oversold. |

## 4. Limitations PREVAIL must acknowledge

- The what-if simulator is a **model-based counterfactual re-forecast**, not a validated causal
  effect. It answers "what does the model predict if this state were different," never "what
  would actually happen if you did this in production." This must be stated in the UI itself,
  not just in documentation (master prompt §2.5, §20).
- Competitor evidence (`Defender`'s 72.5% FPR cross-day result) shows generalization across time
  and attack-type distribution is a genuinely hard, unsolved problem in this exact setting.
  PREVAIL should expect and budget for a real possibility that its own cross-scenario numbers
  are weak, and must report them honestly if so (master prompt §23, §35).
- Competitor stage taxonomies disagree with each other (5-stage vs 7-stage, different orderings).
  This means there is no single "correct" ATT&CK stage vocabulary to benchmark against — PREVAIL
  must document its own mapping's rationale rather than imply it matches an external standard.
- At least one competitor (`AI-Based-Forecasting-SIH2026`) reports metrics that are plausible on
  their face but unusually strong (0 false positives, 99.94% F1) and self-reported without
  independent reproduction. PREVAIL must not treat these as a target to beat or as evidence that
  such performance is realistically achievable — they are unverified claims, not a benchmark.

## 5. Claims PREVAIL must NOT make

- "PREVAIL is the first system to forecast multi-step attack trajectories" — **false**, per
  `AttackForecast` and the academic prior art found.
- "PREVAIL's World Model is novel" — **false** as an architecture-class claim; only the specific
  combination/engineering choices could be argued original, and only with ablation evidence.
- "The what-if simulator shows that isolating Host A prevents lateral movement" — **prohibited**
  causal language (master prompt §2.5). Must always read "the model forecasts a lower
  probability under the simulated intervention."
- "PREVAIL generalizes across attack types/time better than existing systems" — **not to be
  claimed** unless PREVAIL runs the same cross-day/cross-scenario evaluation `Defender` ran and
  actually beats it, with the same rigor, and even then only as a measured result, not a general
  guarantee.
- Any ATT&CK **technique**-level claim (vs tactic/stage-level) without an explicit evidence field
  backing it — per master prompt §18, an LLM (if used at all) must never autonomously invent an
  ATT&CK mapping, and neither should PREVAIL's own heuristics without a recorded rationale.
