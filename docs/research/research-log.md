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

---

## RL-5 — 2026-09-20

**Question:** Following up on OQ-2/D-003 — now that the full synthetic-data pipeline (Milestones
1-13) is built and working, which real public network-security dataset should PREVAIL integrate,
and does any candidate genuinely support multi-stage attack-progression labels (recon -> initial
access -> lateral movement -> C2) rather than just flat attack-type classification?

**Sources checked:** UNB CIC-IDS2017/CSE-CIC-IDS2018 official pages, AWS Open Data registry for
CSE-CIC-IDS2018, Stratosphere Lab CTU-13 page + FAQ + a fetched scenario README/directory listing
(CTU-Malware-Capture-Botnet-43), UNSW-NB15 feature/statistics writeups, CICIoT2023 IEEE DataPort
listing, Engelen et al. "Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case
Study" (documented CICFlowMeter bugs and labeling errors), multiple independent sources on
NSL-KDD/KDD-99 obsolescence. Full citation list in `docs/research/real-dataset-integration.md`.

**Finding:** None of the 5 mainstream candidates (CIC-IDS2017, CSE-CIC-IDS2018, CTU-13, UNSW-NB15,
CICIoT2023) provide native ground-truth multi-stage kill-chain labels. Four of them (all except
CTU-13) are structured as discrete, scheduled attack-tool exercises with flat attack-type labels
and only weak/no temporal-campaign continuity. CTU-13 is the one exception: a genuinely
continuous, multi-hour real botnet capture, but its native labels are only 4 flat categories
(Background/Normal/Botnet/C&C) — only `benign` and `command_and_control` map onto PREVAIL's
stage vocabulary with real evidence; `recon`/`initial_access`/`lateral_movement` are
**unavailable** as ground truth in CTU-13 and must not be invented. Also found: PREVAIL's
ingestion contract expects packet-level rows, but every candidate dataset is distributed
primarily as pre-aggregated flow records (CICFlowMeter/Argus/NetFlow) — meaning the real adapter
needed is a PCAP-to-PacketEvent parser (new code), not a flow-feature mapper, after which
`features/`, `states/`, `sequences/`, `baselines/`, `world_model/`, `evaluation/` need zero
changes. One CTU-13 scenario's truncated pcap (Botnet-43/Neris) is a feasibly small 35MB given
this environment's measured slow/flaky network, versus CIC-IDS2017's 50GB+ PCAPs or
CSE-CIC-IDS2018's ~480GB.

**Decision:** Recommend CTU-13 (specifically, starting with one small scenario, e.g. Botnet-43,
before committing to a multi-scenario download for a proper scenario-level train/test split),
evaluated on a reduced/honestly-scoped stage vocabulary (binary attack/benign + a distinguishable
C&C sub-case), not the full 5-stage synthetic vocabulary. Full reasoning, feature-mapping table,
leakage risks, and a proposed-but-not-implemented integration plan written to
`docs/research/real-dataset-integration.md`. **Stopped after the research document per explicit
instruction** — no adapter code, tests, or pipeline runs against real data in this pass.

**Reason:** Master prompt's "no fake novelty"/"never invent a requirement" discipline extends
directly to labels: presenting an inferred/heuristic stage assignment as if it were the same kind
of ground truth as the synthetic generator's simulator-assigned `attack_stage` would misrepresent
the evidentiary basis of any resulting metric. Temporal continuity was prioritized over raw
popularity/prior-work-volume because it's the property PREVAIL's entire premise (`P(S_t+1|S_t)`,
K-step rollout, "trajectory") depends on — a dataset without it would produce technically-runnable
but conceptually-hollow results.

**Impact:** Real-dataset integration, once implemented, will report on a narrower label set than
the synthetic track for the attack-stage/ATT&CK-mapping/K-step-forecast-of-specific-stage results
— this must be stated explicitly in `README.md`/`docs/limitations.md` once real results exist, and
real-dataset metrics must never be combined into the same score/table as the synthetic F1≈0.823
baseline (which remains the frozen regression reference — new dataset gets its own experiment
namespace under `artifacts/evaluation/real_dataset/`).

## RL-6 — 2026-09-20

**Question:** Is RL-5's CTU-13 recommendation, and the assumptions it rests on, actually correct —
verified against authoritative sources and a real download attempt, not just RL-5's own reasoning?
(User-directed Phase 1 verification step before any adapter code.)

**Sources checked:** `stratosphereips.org/datasets-ctu13` (live fetch), scenario READMEs for
CTU-Malware-Capture-Botnet-42/43/54 (live fetch), direct `curl` connection/download attempts against
`mcfp.felk.cvut.cz` (3 repeated real download attempts, plus HEAD-request probes), a Kaggle/mirror
search for alternative hosting.

**Finding:** Two RL-5 assumptions were wrong (see `DECISIONS.md` D-012 and
`docs/research/real-dataset-integration.md` §9 for full detail): (1) the small ~35-109MB per-scenario
pcap is attack-traffic-only, not the full scenario — the file actually needed for benign+attack
coverage is a separate 843MB-1.2GB truncated full-traffic pcap; (2) labels are unidirectional Argus
with compound label strings, not "bidirectional, 4 flat categories." More consequentially: real
download attempts against the required file's host showed ~65% per-attempt connection failure and
~17 KB/s sustained transfer on the one successful attempt — extrapolating to 14-20+ hours for the
actually-needed file, with a high chance of failing mid-transfer.

**Decision:** STOP before writing any adapter code (Phase 2 of the approved plan). Corrected
`docs/research/real-dataset-integration.md` in place. Reported the blocker and options back to the
user rather than proceeding, silently working around it, or picking a fallback unilaterally.

**Reason:** This is precisely the situation the approved plan's own "STOP CONDITIONS" section
anticipated ("CTU-13 cannot be obtained/accessed as expected... do not hide these issues") — treating
it as designed-for rather than as a failure to route around quietly.

**Impact:** No CTU-13 adapter code exists yet. `README.md`/`docs/limitations.md` continue to
correctly state real-dataset integration as the top open item; this entry is the record of why it's
still open despite two full research passes, so a future session doesn't have to re-derive the same
finding from scratch.
