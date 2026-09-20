# PREVAIL — Research Log

Format per master prompt §33: Date / Question / Sources checked / Finding / Decision / Reason / Impact

---

## RL-1 — 2026-09-20

**Question:** Is `/mnt/data/bugbounty guide.pdf` present, and can it serve as the primary source
as the master prompt requires?

**Sources checked:** Direct filesystem listing of `/mnt/data`.

**Finding:** Path does not exist in this environment.

**Decision:** Proceed using convergent secondary evidence (public SIH26153 repos) for PS
identity/requirements, log the gap in `open-questions.md` (OQ-1), do not invent or assume PDF
contents.

**Reason:** Master prompt rule 0.6 requires recording ambiguity rather than guessing.

**Impact:** `source-requirements.md` is built on secondary, not primary, sourcing — flagged
explicitly throughout that document. Requirement confidence is "high" not "verified."

---

## RL-2 — 2026-09-20

**Question:** What is the actual SIH26153 problem statement, given the primary source is
unavailable?

**Sources checked:** Web search ("SIH26153 problem statement", "SIH 2025/2026 26153 network
attack prediction"); direct fetch of 4 GitHub repos claiming to be SIH26153 submissions
(`HowSuyash/AttackForecast`, `syednzaheer/SIH-P.S.-26153-Defender`,
`abdulmuqeeth-ai/AI-Network-Attack-Forecasting`, `Kshitiz-Khandelwal/AI-Based-Forecasting-SIH2026`);
attempted fetch of the SIH 2026 master-catalogue PDF and the CodeHuntersAcademy PS explorer (both
failed to yield extractable text for PS 26153 specifically).

**Finding:** 4 independent repos converge on: PS 26153, organization NTRO, title "AI based
Network Attack Forecasting from Network Traffic Data," theme Blockchain & Cybersecurity,
software category, core mandate = learn `P(S_{t+1}|S_t)` and forecast multi-stage infiltration
mapped to MITRE ATT&CK, instead of independent-flow binary classification.

**Decision:** Treat this as the working PS definition, cross-checked against (and found
consistent with) the master prompt's pre-existing FR-01…FR-17 list.

**Reason:** Independent convergence across unrelated teams is reasonable secondary evidence in
the absence of the primary PDF; no conflicting account was found.

**Impact:** No architecture change. Confirms the master prompt's requirement list is an accurate
PS extraction. Literal PDF text remains unverified (OQ-3) — should be re-checked if the PDF
becomes available.

---

## RL-3 — 2026-09-20

**Question:** What does existing prior art (academic + SIH26153-specific) already provide, and
what, if anything, can PREVAIL legitimately claim as differentiation?

**Sources checked:** WebSearch across "temporal world model network intrusion forecasting",
"multi-step cyber attack forecasting GRU transformer MITRE ATT&CK"; direct fetch of 4 SIH26153
repos (see RL-2) plus search-level review of ~7 academic/adjacent items (KillChainGraph,
LSTM-Markov attack-chain forecasting, TCN-NIDS, TSAN, Modular Framework for Intrusion Predictors,
Temporal Analysis Framework for IDS, SoK MITRE ATT&CK).

**Finding:** The mandatory core (World Model, K-step rollout, ATT&CK mapping, explainability) is
already implemented, in a scientifically serious form, by at least one public SIH26153 team
(`AttackForecast`). No inspected prior-art item — academic or SIH-specific — implements a
defensive what-if/counterfactual intervention simulator; one competitor explicitly states it as
absent.

**Decision:** PREVAIL will not claim novelty for the mandatory core. PREVAIL's primary
differentiation claim is the what-if intervention simulator, explicitly labeled throughout as an
extension beyond the mandatory PS requirement, with strict non-causal language.

**Reason:** Per master prompt §2.3/§35: no fake novelty, do not claim novelty without prior-art
evidence. The intervention simulator is the one item with actual evidenced absence across all
inspected competitors.

**Impact:** `differentiation.md` written accordingly. Also surfaced OQ-4 (un-inspected repos that
could still close this gap) and OQ-5 (competitor self-reported metrics that should not be treated
as a target).

---

## RL-4 — 2026-09-20

**Question:** Is a real telemetry dataset available in this environment, and if not, what is the
right sequencing for dataset acquisition vs. pipeline validation?

**Sources checked:** Filesystem check (`data/raw/` empty); review of what datasets competitor
repos use (CTU-13, CSE-CIC-IDS2018, CIC-IDS-2017, UNSW-NB15, CICIoT2023).

**Finding:** No dataset bundled. All commonly-used datasets in this space are external
downloads of non-trivial size.

**Decision:** Build and validate the pipeline (windowing → state → sequence → leakage checks)
against a clearly-labeled synthetic dataset first; treat real-dataset acquisition (starting with
CTU-13 as the smallest/most permissively-licensed competitor-used option) as the next step, not
a blocker for pipeline-correctness work.

**Reason:** Master prompt §2.2 — prove the simplest scientifically valid version first (data
validity, windowing validity, state validity) before adding sophistication; do not let a large
download block that validation work.

**Impact:** Recorded as OQ-2 with an explicit warning: synthetic-data results must never be
presented as PS-evidence of real detection/forecasting performance, only as pipeline validation.
