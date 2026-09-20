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

---

## D-009: Interventions are packet-level filters, not feature-level edits

**Context:** Building the what-if simulator (Milestone 9), the natural-seeming shortcut is to directly edit a state's feature vector (e.g. set `unique_dst_ip_count -= 1` to simulate isolating a host). But PREVAIL's feature registry deliberately has no raw-IP features (data-contract.md: avoids host-identity overfitting) — there is nothing to "edit" that corresponds to a specific host, and hand-editing one aggregate feature would leave the other 58 correlated features inconsistent with a real filtered-traffic scenario.

**Alternatives:** (a) feature-level edits, fast but dishonest — the "modified state" wouldn't be a state any real filtered packet capture could actually produce; (b) packet-level filtering — apply the intervention as a filter on the current window's raw packets, then recompute that window's features through the exact same `features/` pipeline used everywhere else.

**Chosen option:** (b). Implemented by factoring `compute_window_row` out of `states/builder.py` (previously inline in `build_states`'s loop) so `intervention/simulator.py` can call the identical code path on a filtered packet set.

**Reason:** Master prompt: "Only support interventions that can be represented honestly in the state representation." A feature-level edit cannot be honest when the representation was specifically designed not to contain the thing being intervened on (host identity). Packet-level filtering keeps the "modified simulated state" a real, internally-consistent state — every one of the ~59 features is recomputed together, not just the one an engineer thought to touch.

**Trade-offs:** Requires retaining access to raw packets alongside the states table at simulation time (not just the precomputed feature parquet) — acceptable since the API layer will need the raw capture available anyway for the initial `/analyze` step.

---

## D-011: `pyarrow` was an undeclared dependency — found by the offline Docker smoke test doing exactly its job

**Context:** Local development installed `pyarrow` ad hoc (`pip install pyarrow`, for parquet I/O) directly into `.venv`, but it was never added to `pyproject.toml`. Everything worked locally because the venv had it installed regardless of what was declared. The first `docker compose build` + smoke test run (built purely from `pyproject.toml`, no inherited venv state) crashed on startup: `ImportError: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'` when `DatasetStore._load_demo_dataset()` called `pd.read_parquet`.

**Chosen option:** Added `pyarrow` to `pyproject.toml` dependencies.

**Reason/evidence:** This is precisely the class of bug an offline/reproducibility smoke test exists to catch — an undeclared dependency that a local dev environment silently papers over. It would have shipped broken to anyone building the Docker image fresh, or onto a clean machine, without ever surfacing in local `pytest` runs (which also ran against the same already-populated `.venv`).

**Secondary finding, same debugging pass**: `docker compose build api 2>&1 | tail -40` reported `exit code 0` on a build that had actually *failed* (`pip install` hit a `ReadTimeoutError` on this environment's slow/flaky connection to PyTorch's CDN) — because in a `cmd1 | cmd2` pipeline, the shell's exit code is `cmd2`'s (`tail`'s, which succeeds trivially), not `cmd1`'s. This produced a false "success" signal that would have let a broken image pass unnoticed. Fixed by redirecting to a log file and checking `$?` directly instead of piping through `tail`, and by reordering the Dockerfile so `torch` installs in its own early layer (rarely invalidated) ahead of `COPY src/` (invalidated on every code change) — both a build-speed fix and, incidentally, why the *second* rebuild attempt only needed to redownload the small `pip install -e .` layer instead of the full ~200MB torch wheel again.

**Trade-offs:** None — this is a straightforward correctness fix plus a general "don't trust exit codes through an unguarded pipe" lesson worth keeping in mind for any future CI/build scripting in this repo.: Add an out-of-distribution sanity flag to every intervention output, after the first real intervention test moved P(attack) the WRONG direction

**Context:** First end-to-end run of the what-if simulator (`scripts/intervention_demo.py`) on a held-out attack scenario showed BOTH tested interventions (`block_destination_port`, `isolate_host`) *increasing* forecast P(attack) rather than decreasing it (see `docs/experiments/intervention.md` for full numbers). Before concluding anything about why, the first thing to rule out was "is the modified state simply nonsense/out-of-distribution, and the model is extrapolating wildly."

**Chosen option:** Added `intervention.simulator.out_of_distribution_score` / `is_out_of_distribution` — mean |z-score| of the modified state against the World Model's own training-distribution mean/std, threshold calibrated empirically at 1.15 (the ~92nd percentile of mean-|z| across all 2400 real synthetic states, not an arbitrary guess).

**Evidence:** Both tested interventions' modified states scored 0.55-0.58, well within the normal range — ruling out "obviously broken input" as the explanation for the counter-intuitive result. The result is therefore an honest, in-distribution model limitation (see `docs/experiments/intervention.md` for the leading hypothesis: the training data contains zero examples of a post-intervention window, so neither model has ever been taught what successful defense looks like), not a pipeline bug.

**Reason:** A what-if simulator that can silently feed a model a nonsensical, never-seen-anything-like-it input and present the output as a confident forecast is a real safety/honesty risk for a security tool. A cheap sanity check that can at least distinguish "confidently wrong because untrained-on-this" from "confidently wrong because the input itself is garbage" is worth having even at V1, and directly enabled the honest root-cause writeup in `docs/experiments/intervention.md` instead of a guess.

**Trade-offs:** This is a coarse, non-rigorous OOD detector (mean |z| across independent per-feature scores, ignoring feature correlations) — a proper Mahalanobis-distance or learned density model would be more rigorous. Flagged as a possible follow-up, not blocking, since even this coarse version already ruled out the simplest failure mode.
