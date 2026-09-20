# PREVAIL — Decision Log

Format per master prompt §34: Decision / Context / Alternatives / Evidence / Chosen option / Reason / Trade-offs.

---

## D-001: Primary source PDF is unavailable — proceed on master-prompt spec + independent PS research

**Context:** Master prompt names `/mnt/data/bugbounty guide.pdf` as the primary source. That path does not exist in this environment (verified via `ls`, 2026-09-20).

**Alternatives:** (a) block and ask the user to supply the file; (b) proceed using the master prompt's own already-extensive requirement text (sections 1, 6) plus independent research into the official SIH26153 problem statement.

**Evidence:** User explicitly instructed full autonomous execution; the master prompt itself already contains a detailed, internally-consistent requirement set (FR-01..FR-17) that does not depend on the missing PDF's contents being read to be actionable.

**Chosen option:** (b) — proceed, treat the master prompt's FR list as the working requirement set, and independently research the official SIH26153 PS text to cross-check/confirm terminology and mandatory scope (delegated to research fork, see `docs/research/source-requirements.md`).

**Reason:** Blocking on a file that cannot be supplied in this environment would stop all progress; the master prompt already encodes the requirements in enough detail to build against, and cross-checking against the real PS closes the gap responsibly.

**Trade-offs:** Any requirement that exists *only* in the missing PDF and not in the master prompt text or the public PS will be missed until/unless the user supplies the file. Flagged in `docs/research/open-questions.md`.

---

## D-002: Repository root is `/home/gokulraj/sih` directly, not a nested `prevail/` folder

**Context:** Master prompt's example tree roots everything under a `prevail/` directory name.

**Alternatives:** (a) create `sih/prevail/...`; (b) treat `sih/` itself as the project root and place the tree directly inside it.

**Chosen option:** (b).

**Reason:** `sih/` was already the dedicated, empty-except-for-the-prompt working directory for this single project; nesting `prevail/` inside it adds a redundant path segment with no benefit.

**Trade-offs:** None material — package name (`prevail`) is preserved at `src/prevail/`, so imports and packaging are unaffected.

---

## D-003: No bundled network telemetry dataset — MVP uses a documented synthetic-validation dataset, real dataset integration tracked as open item

**Context:** No PCAP/flow dataset is present in this environment; downloading a large real benchmark (CICIDS2017/2018, CTU-13, etc.) is possible (internet access confirmed) but multi-GB and time-costly, and real-dataset licensing/registration steps may not be completable autonomously in one session.

**Alternatives:** (a) attempt to download a large real IDS dataset immediately before building any pipeline code; (b) build the full pipeline (ingestion → features → states → sequences → baseline → world model → rollout) against a small, clearly-labeled **synthetic** telemetry generator first, proving the architecture is scientifically valid per master-prompt §2.2, then integrate a real dataset as the next increment.

**Chosen option:** (b).

**Reason:** Master prompt §2.2 explicitly requires proving data validity, temporal window validity, state validity, baseline, one-step, K-step, and evaluation trustworthiness *before* adding sophistication — this is dataset-shape-agnostic. A synthetic generator with explicit, documented attack-stage ground truth (recon → initial access → lateral movement → C2, plus benign traffic) lets every pipeline stage be built and unit/property-tested correctly first. All results produced against synthetic data will be labeled **"synthetic validation data — not a real-world benchmark result"** everywhere they appear (metrics reports, docs/experiments/*), per master-prompt §2.3/§35 (no fabricated benchmark claims).

**Trade-offs:** SIH judges will expect real-dataset evaluation eventually. Tracked as the top open item in `docs/research/open-questions.md`; real-dataset ingestion path is built into `ingestion/` from the start (flow-CSV format compatible with CICFlowMeter-style exports) so swapping in a real dataset later does not require re-architecting.

---

## D-004: Python 3.12 / venv at `.venv`, PyTorch CPU-only build

**Context:** Environment has Python 3.12.3, no GPU assumed/available.

**Chosen option:** Standard `venv` at `.venv/`, `torch` installed from the CPU wheel index (`download.pytorch.org/whl/cpu`) to avoid a large unnecessary CUDA download and keep the environment genuinely offline-portable.

**Reason:** Matches the offline/air-gapped non-functional requirement (NFR) and the "start with a small Transformer" guidance (§13) — CPU is sufficient for the small model sizes specified.

**Trade-offs:** Training larger models later would need GPU provisioning; out of scope for V1.

---

## D-005: Window attack-stage labeling is presence-based, not majority-vote

**Context:** First implementation of `_window_attack_stage` (states/builder.py) used pure majority vote across packets in a window. Running the pipeline against the synthetic dataset showed **zero** windows labeled `initial_access` or `command_and_control` despite both stages being generated — every one of those windows' sparse attack packets (a handful of exploit attempts or a single C2 beacon) was outnumbered by concurrent benign background traffic (4-10 pkt/s) and outvoted to `benign`.

**Alternatives:** (a) keep majority vote, accept that low-volume attack stages are undetectable at the labeling stage; (b) presence-based labeling — any non-benign stage with packet count >= a small threshold (2) wins, regardless of benign volume in the same window.

**Evidence:** Post-fix label distribution moved from `{benign: 2148, recon: 136, lateral_movement: 116}` (initial_access=0, c2=0) to a distribution including all 4 attack stages (see `artifacts/data_quality_report.html`, regenerated after the fix).

**Chosen option:** (b).

**Reason:** Real low-and-slow attack techniques (C2 beaconing, slow exploit attempts) are *specifically* low-volume relative to background traffic — that's what makes them hard to detect and exactly what a forecasting system needs to catch. A labeling rule that defines them out of existence whenever benign traffic is present would make the ground truth unfit for the problem PREVAIL is meant to solve.

**Trade-offs:** Presence-based labeling is more sensitive to the `MIN_ATTACK_PACKET_PRESENCE` threshold (currently 2, chosen to filter single-packet noise while catching real C2 beacons/exploit bursts) — worth revisiting once a real dataset is integrated, since its packet-per-window density will differ from the synthetic generator's.

---

## D-006: Logistic Regression baseline predicts one-step-ahead, not same-instant, attack label

**Context:** Master prompt Phase 9 is deliberately vague about baseline input/output ("current state / allowed historical aggregate features" -> "attack probability / required baseline target"), likely because most competitor implementations use it as a plain same-instant classifier.

**Alternatives:** (a) same-instant baseline: predict whether the *current* window is an attack, standard IDS-style; (b) one-step-ahead baseline: predict whether the *next* window is an attack, using only the current window's features as input.

**Chosen option:** (b).

**Reason:** PREVAIL's central claim (master prompt Sec 1) is that a World Model forecasts *future* states, distinct from a same-instant classifier. For FR-15 ("evaluate against baseline") to be a meaningful test of that claim, the baseline must be asked to solve the *same forecasting task* the World Model solves (predict t+1 from t), not an easier same-instant classification task — otherwise a baseline "win" or "loss" wouldn't isolate the thing PREVAIL is actually claiming to do better.

**Evidence:** Implemented in `baselines/logistic_regression.py::current_state_input` (takes the last historical timestep of each built sequence as input, `y_label` of the sequence's target window as the one-step-ahead label). First run on synthetic data: test F1 0.823, ROC-AUC 0.870, FPR 0.050 — plausible, not suspiciously perfect (contrast with OQ-5's flagged competitor claiming 0 FPs), which is itself weak evidence against a labeling/leakage bug.

**Trade-offs:** This makes the baseline harder to beat than a same-instant classifier would be (forecasting is intrinsically harder than nowcasting), which is the honest comparison PREVAIL needs, not the easiest one to win.

---

## D-007: Single regression head (Huber loss) for the World Model's state prediction, not separate per-type heads

**Context:** Master prompt Phase 11 asks for separate continuous/binary/categorical loss heads when a state mixes feature types.

**Chosen option:** Single Huber-loss regression head over the full 59-feature vector; a small auxiliary cross-entropy stage-classification head is trained jointly (weight 0.3) to sharpen the representation, but that head lives outside the state-prediction path used for K-step rollout.

**Reason:** PREVAIL v1's feature registry (data-contract.md Sec 3) is homogeneously continuous/ratio-valued -- no one-hot categorical or true binary fields ended up in the feature vector itself, so Phase 11's premise (mixed types needing mixed losses) doesn't apply to this feature set. Huber loss is used instead of plain MSE specifically because several features (byte/packet counts) are heavy-tailed and MSE would let a few extreme-traffic windows dominate the gradient.

**Trade-offs:** If a future feature version adds genuinely categorical/binary fields (e.g. a one-hot protocol encoding instead of ratios), this decision should be revisited and the multi-head design implemented as originally specified.

---

## D-008: One-step feature-level error must be reported in standardized units, not raw units

**Context:** First run of `evaluation.one_step.feature_level_error` ranked "worst predicted features" by raw MSE and put `temporal__rolling_var_bytes_sum` at the top with an MSE of ~1.6e16 -- a number so large it's meaningless on its own, and it crowded out genuinely informative ranking of which features the model actually struggles with.

**Chosen option:** Report both raw-unit MAE/MSE (for human-readable magnitude) and standardized MAE/MSE (error divided by the train-set feature std, i.e. the same units the model is actually trained/optimized in) -- ranking of "worst" features uses the standardized value.

**Evidence:** Post-fix, overall normalized MSE = 0.369 on the held-out test scenarios (a "predict the training mean" baseline would score ~1.0 by construction of the normalization), and the worst-ranked features became `tcp_fin_ratio`, `delta_packets_sum`, `delta_new_connection_count` -- plausible, moderate-difficulty features, not an artifact of feature scale.

**Reason:** Raw-unit MSE across features with wildly different natural scales (a [0,1] ratio vs. a rolling variance of byte-count sums) isn't comparable and produces a misleading "worst features" ranking that would mislead any later ablation/architecture decision made by reading this report.

**Trade-offs:** None material -- this is a strictly more correct evaluation; raw units are kept alongside for interpretability, not removed.
