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
