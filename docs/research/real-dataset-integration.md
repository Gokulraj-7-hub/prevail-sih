# PREVAIL — Real-Dataset Integration Research

Date: 2026-09-20. Written in response to the top-tracked open item across this repo (`README.md`, `docs/limitations.md`, `docs/acceptance-criteria.md`, `docs/research/open-questions.md` OQ-2, `DECISIONS.md` D-003).

**Status as of the Phase 1 verification pass (second research pass, same date): STOPPED before implementation.** The initial recommendation below (§1-§8) was produced by a research-only pass that did not attempt an actual download. A follow-up verification pass fetched authoritative sources directly and attempted real downloads, and found two of the first pass's assumptions were **wrong** (§9), plus a **hard feasibility blocker** (§10) that meets the project's own "CTU-13 cannot be obtained/accessed as expected" stop condition. See §9-§11 for the corrected findings — read those before treating anything in §1-§8 as settled. Per instruction, code implementation did not proceed; this document and `DECISIONS.md` (D-012) were updated first, as required before any adapter code is written.

**Scope discipline**: per instruction, this document does not fabricate attack-stage labels. Where a candidate dataset's native ground truth does not support a specific stage in PREVAIL's `ATTACK_STAGES` vocabulary (`benign, recon, initial_access, lateral_movement, command_and_control` — `src/prevail/common/schema.py`), that stage is marked **UNAVAILABLE** for that dataset, not inferred or approximated as if it were ground truth.

---

## 0. What the existing pipeline actually requires (re-verified on-disk before researching datasets)

- **Ingestion contract** (`preprocessing/clean.py::REQUIRED_COLUMNS`, `common/types.py::PacketEvent`): one row per **packet**, not per flow: `timestamp, scenario_id, src_ip, dst_ip, src_port, dst_port, protocol, tcp_syn, tcp_ack, tcp_fin, tcp_rst, tcp_psh, tcp_urg, ttl, tcp_window, fragmented, payload_size, retransmission[, attack_stage]`. This is the single most consequential compatibility fact: **every mainstream candidate below is distributed primarily as pre-aggregated flow records (CICFlowMeter/Argus/NetFlow-style — one row per flow, not per packet), not as packet-level CSVs.** None of them match PREVAIL's ingestion shape natively.
- **Feature computation** (`features/{flow,packet,temporal}.py`) all operate on a window's raw *packets* and derive flow-level, packet-level, and temporal features from them internally — they do not consume a dataset's pre-computed flow features directly. This means the 59 features are not really "mapped from a dataset's native fields" one-for-one; they are *recomputed by PREVAIL's own code from raw packets*, exactly as they are for the synthetic generator today.
- **Consequence**: the smallest real adapter is not a flow-CSV-to-feature mapper — it is a **PCAP → `PacketEvent` parser**, after which every downstream stage (`features/`, `states/`, `sequences/`, `baselines/`, `world_model/`, `evaluation/`) needs **zero changes**. This was already anticipated in `data-contract.md` §5 ("packet_features nullability... populated whenever the source data includes packet-level fields... for real PCAP ingestion") but not yet implemented — `docs/limitations.md` and `threat-model.md` both flag binary PCAP parsing as not yet built.
- `states/builder.py::_window_attack_stage` (presence-based labeling, `MIN_ATTACK_PACKET_PRESENCE=2`, D-005) and `sequences/split.py::scenario_train_test_split` (scenario-level, stratified by `has_attack`) are dataset-agnostic and reusable as-is, **provided** the real dataset can be organized into independent "scenario" units the way the synthetic generator's 40 scenarios are. This is a real constraint discussed in §5 below — most real datasets don't ship as cleanly-scenario-partitioned data.
- Existing tests (`tests/property/test_no_label_leakage.py`, `test_windowing.py`, `tests/unit/test_interventions.py`, `tests/unit/test_security.py`, `tests/integration/test_api.py`) all operate on the synthetic generator's output shape or on the API layer — none currently exercise a real PCAP parse path, so a real-dataset adapter needs new tests, not just new code.

---

## 1. Candidate datasets — comparison table

| Dataset | Native format | Packet-level access | Native attack-stage/kill-chain labels | Temporal continuity | Total size | Access |
|---|---|---|---|---|---|---|
| **CTU-13** (Stratosphere Lab) | Flow (Argus bidirectional NetFlow) + raw/truncated PCAP | **Yes** (truncated-but-header-intact PCAP per scenario) | Partial — 4 flat categories (Background/Botnet/C&C/Normal), no recon/lateral-movement distinction | **Yes** — continuous multi-hour real botnet captures, one malware family per scenario | 1.9GB (all 13) / scenario-dependent, one example scenario's truncated pcap = 35MB | No registration; citation required (Garcia et al. 2014, Computers & Security) |
| CIC-IDS2017 | Flow (CICFlowMeter, 80 features) + full PCAP | Yes (full pcap) | **No** — flat attack-type label per exercise (Mon benign, Tue brute-force, Wed DoS, Thu web/infiltration, Fri botnet/scan/DDoS) | Weak — each attack type is a scheduled, largely isolated exercise on its own day, not a continuous multi-stage campaign | PCAPs ~50.1GB total (11+11+13+7.8+8.3GB across 5 days); CSVs smaller (not independently confirmed) | Direct download, no registration; **documented data-quality issues** (see §4) |
| CSE-CIC-IDS2018 | Flow (CICFlowMeter-V3, 80 features) | Yes (full pcap) | **No** — flat per-day attack scenario label (Brute-force, Heartbleed, Botnet, DoS, DDoS, Web, Infiltration) | Weak, same structure as CIC-IDS2017 | ~477GB raw PCAP, ~484GB total (AWS `s3://cse-cic-ids2018`) | AWS Open Data, no registration, but **far too large for this environment's measured ~100kbps-1Mbps connection** |
| UNSW-NB15 | Flow (Argus + Bro-IDS, 49 features) | Not verified whether raw pcap is redistributed alongside | **No** — 9 flat attack categories (Analysis, Backdoor, DoS, Exploits, Fuzzers, Generic, Reconnaissance, Shellcode, Worms) | Not verified — "100GB captured over two days"; unclear if attacks are continuous multi-stage campaigns or scheduled exercises like CICIDS | ~100GB raw capture (2 days) | UNB CIC hosts it; access terms not independently re-verified this pass |
| CICIoT2023 | Flow/packet CSV, PCAP also offered | Yes (pcap available) | **No** — 7 flat attack classes (DDoS, DoS, Recon, Web, Brute Force, Spoofing, Mirai) over 33 attack subtypes | Not verified — IoT testbed, attacks executed by devices against devices; not described as continuous multi-stage campaigns in what was found | Very large (47M+ flows, "449,144,189 samples" per one source — treat that specific figure as **Not verified**, sources were inconsistent) | Kaggle / UNB / IEEE DataPort |
| NSL-KDD / KDD Cup 99 | Flat feature records, no raw packets | No | **No** | No — i.i.d. records, not a capture | Small (~tens of MB) | Freely available | **Excluded** — see §4, well-documented obsolescence (1998 traffic, synthetic DARPA testbed origin) |

**Sources**: [UNB CIC-IDS2017](https://www.unb.ca/cic/datasets/ids-2017.html), [Stratosphere CTU-13](https://www.stratosphereips.org/datasets-ctu13), [Stratosphere FAQ](https://www.stratosphereips.org/datasets-faq), [CTU-Malware-Capture-Botnet-43 index](https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-43/), [AWS Open Data CSE-CIC-IDS2018](https://registry.opendata.aws/cse-cic-ids2018/), [fkie-cad COMIDDS CSE-CIC-IDS2018](https://fkie-cad.github.io/COMIDDS/content/datasets/cse_cic_ids2018/), [UNSW-NB15 feature discussion](https://www.researchgate.net/figure/Features-of-UNSW-NB15-dataset_tbl1_324601933), [CICIoT2023 IEEE DataPort](https://ieee-dataport.org/documents/ciciot2023-dataset), [Engelen et al., "Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study"](https://intrusion-detection.distrinet-research.be/WTMC2021/Resources/wtmc2021_Engelen_Troubleshooting.pdf), [fkie-cad NSL-KDD](https://fkie-cad.github.io/COMIDDS/content/datasets/nsl_kdd_dataset/).

---

## 2. The single most important filter: none of these have genuine multi-stage kill-chain ground truth

This is the headline finding, and it constrains every option, not just the recommendation:

- **CIC-IDS2017, CSE-CIC-IDS2018, UNSW-NB15, CICIoT2023** all label traffic by **attack type/tool**, executed as **discrete, scheduled exercises** (e.g., "Tuesday 9:20-10:20am: FTP brute force"), not as one continuous attacker campaign that progresses through recon → initial access → lateral movement → C2. There is no native evidence in any of them for PREVAIL's specific stage vocabulary beyond "this flow belongs to attack-type X." Building a `recon`/`initial_access`/`lateral_movement` distinction from these would require **inventing** a stage assignment for each attack type — exactly what the instruction says not to do.
- **CTU-13** is the partial exception, and the reason it is recommended below: it is a **real, continuous, multi-hour capture of live botnet malware behaving on its own schedule** (not a scripted attack-tool exercise), which structurally matches PREVAIL's premise of temporal state evolution far better than a day-partitioned exercise dataset. But its *native labels* are still only 4 flat categories: `Background`, `Normal`, `Botnet` (general infected-host traffic, both `From-Botnet`/`To-Botnet` directional variants), and `C&C Channels` (command-and-control specifically) — confirmed via the Stratosphere dataset page and a scenario-level README fetched directly.
- **Consequence for PREVAIL's stage vocabulary against CTU-13**: only `benign` (Normal + Background) and `command_and_control` (C&C Channels) are directly evidenced. `recon`, `initial_access`, and `lateral_movement` are **UNAVAILABLE** as ground truth in CTU-13's native labels — most CTU-13 captures begin *after* the bot is already installed and active, so there generally isn't a captured "initial access" moment at all, and the dataset does not separately flag scanning/lateral-movement sub-behavior within the generic `Botnet` category. One competitor repo already inspected in `docs/research/prior-art.md` (`HowSuyash/AttackForecast`) built its own heuristic rules to derive a fuller stage vocabulary from CTU-13 — that is their choice to document and defend, not evidence PREVAIL can reuse as ground truth without repeating the same inference step itself, which this document explicitly declines to do.

**Recommendation follows from this**: real-dataset integration should evaluate PREVAIL's World Model and baseline on a **reduced, honestly-scoped stage vocabulary** for the real-dataset track — realistically `benign` vs `attack` (binary), with `command_and_control` kept as a distinguishable sub-case where the C&C label applies, and `recon`/`initial_access`/`lateral_movement` reported as **not evaluable on this dataset** rather than populated with invented labels. This is a real, load-bearing scope reduction versus the synthetic track, and must be stated plainly wherever real-dataset results are reported (see §7).

---

## 3. Recommended dataset: CTU-13

### Why (evidence-based, not just "it's what a competitor used")

1. **Temporal suitability wins over popularity.** Per the framing above, CTU-13 is the only candidate that is a genuinely continuous, multi-hour capture of an attacker's (malware's) own behavior over time, rather than a sequence of scheduled, disconnected attack-tool exercises. PREVAIL's entire premise — `P(S_{t+1}|S_t)`, K-step rollout, attack *trajectory* — depends on there being a real trajectory in the data. CIC-IDS2017/2018/UNSW-NB15/CICIoT2023 do not obviously have one; CTU-13 does.
2. **Packet-level access exists and is small enough to be feasible.** The `capture20110811-neris.pcap` (one CTU-13 scenario, "Botnet-43"/Neris) truncated file is **35MB** — realistically downloadable even on this environment's measured slow connection (this session observed sustained rates as low as ~70-130kbps and at least one outright timeout on a ~200MB PyTorch wheel; 35MB at even 100kbps is ~45 minutes, plausible). The Stratosphere blog post confirms the truncation preserves full TCP/UDP/ICMP headers ("still possible to read the complete TCP, UDP and ICMP headers") — meaning `ttl`, `tcp_window`, TCP flags, and (from the IP total-length header field, not the possibly-truncated payload bytes) `payload_size` should all remain derivable even though payload *content* is cut for privacy. This was **not independently verified by actually parsing a file** in this research-only pass — flagged as the first thing to confirm before writing adapter code.
3. **No registration barrier.** Free download, citation-only requirement (confirmed via Stratosphere FAQ).
4. **Individually-downloadable scenarios** (13 separate scenario URLs, `CTU-Malware-Capture-Botnet-42` through `-54`) let the team start with one small scenario and add more incrementally, rather than committing to a monolithic download up front.
5. **The one honest cost**: only a reduced stage vocabulary is evidenced (§2). This is accepted, not hidden — the alternative (CICIDS-family datasets) doesn't offer a *better* stage story despite offering richer flat attack-type labels; it offers a fundamentally different (weaker, for PREVAIL's purposes) temporal story.

### Why not the alternatives, briefly

- **CIC-IDS2017 / CSE-CIC-IDS2018**: richer flat attack-type labels and much more widely used in the ML-IDS literature, but (a) no multi-stage progression evidence, same problem as UNSW-NB15/CICIoT2023 but with more published prior work to compare against; (b) CIC-IDS2017's PCAPs alone are 50GB, CSE-CIC-IDS2018 is ~480GB — both impractical on this environment's measured bandwidth even if a subset were selected, since the smallest single day (Thursday, 7.8GB) still dwarfs CTU-13's 35MB single-scenario pcap by ~220x; (c) CICIDS2017 has a **documented, citable data-quality critique**: Engelen et al. ("Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study") found packet misordering, packet duplication, mislabeled attacks, a CICFlowMeter implementation bug that encodes absolute timestamps into Active/Idle duration statistics, and a duplicated `Fwd Header Length` feature — this is exactly the kind of "spurious separability via non-behavioral artifact" leakage risk the instruction asked to check for, and it is real and citable, not a synthetic worry. **Not disqualifying if the CICFlowMeter CSV were used naively** — but PREVAIL doesn't plan to ingest the CICFlowMeter CSV at all (per §0, we parse packets and recompute features ourselves), so most of these specific tool-bugs would not directly propagate into PREVAIL's own feature computation. Still weighs against CICIDS-family as the primary pick given the temporal-continuity gap is the more fundameuntal problem.
- **UNSW-NB15**: flat 9-category labels, no confirmed evidence of continuous multi-stage campaigns; packet-level pcap availability not independently confirmed this pass. Deprioritized pending further research if CTU-13 doesn't pan out.
- **CICIoT2023**: modern and large, but IoT-device-vs-IoT-device attacks in a testbed, 7 flat classes, no kill-chain narrative found in what was searched; also very large.
- **NSL-KDD/KDD Cup 99**: excluded outright. 1998 DARPA-testbed-derived synthetic traffic, i.i.d. records with no timestamps suitable for windowing, and well-documented in the literature as obsolete for anything beyond legacy-benchmark comparison (multiple sources confirm this independently, see §1 sources).

---

## 4. Leakage risks

- **CICFlowMeter-specific bugs (Engelen et al.)**: not directly applicable to PREVAIL's CTU-13 plan, since we would parse raw packets ourselves rather than ingest CICFlowMeter's flow CSV (§0, §3). Documented here because the instruction explicitly asked about it, and because it's a reason to be skeptical of any published CICIDS2017/2018 benchmark number PREVAIL might otherwise be tempted to compare against.
- **CTU-13-specific leakage risk, genuinely new for this dataset**: the label files are **flow-level** (Argus bidirectional netflow), while PREVAIL needs **packet-level** `attack_stage`. The adapter must join each parsed packet to its flow's label by matching the flow 5-tuple + time window against the labeled netflow file — this join key must be constructed carefully (protocol-aware, both directions of a bidirectional flow) or packets could silently inherit the wrong label. This is a new correctness risk `tests/` does not currently cover and must be unit-tested before trusting any resulting `attack_stage` column.
- **Single-scenario temporal leakage risk**: if only one CTU-13 capture is used, there is no natural second "scenario" to hold out — see §5, this is the main structural risk and drives the split-strategy recommendation.
- **Host-identity leakage**: PREVAIL's feature registry already excludes raw IPs by design (data-contract.md), which happens to also protect against a CTU-13-specific risk: the botnet's C2 server IP is a fixed, small set of addresses across the whole capture, so a naive "IP as feature" approach would let a model trivially memorize the C2 IP rather than learn behavioral signal. PREVAIL's existing design is already leakage-safe here, no new work needed.

---

## 5. Train/test split strategy

PREVAIL's `sequences/split.py::scenario_train_test_split` splits at the **scenario_id** level, stratified by whether the scenario contains an attack — never within a scenario, never a random window shuffle. CTU-13 does not ship a single capture pre-partitioned into 40 independent sessions the way the synthetic generator does. Two honest options:

1. **Recommended: multi-scenario split.** Use several of CTU-13's 13 independently-downloadable scenario captures as the natural `scenario_id` unit — each scenario is a different botnet family captured on a different day, which is a legitimate, non-arbitrary session boundary (arguably a *more* realistic scenario boundary than the synthetic generator's own, since each is a genuinely independent real capture). Train on some scenarios, test on entirely different ones — directly analogous to PREVAIL's existing approach, zero changes to `split.py` needed. **Cost**: downloading N scenario pcaps instead of 1, multiplying the (already nontrivial, see §3) download time by N. A minimum defensible split is probably 3-4 scenarios (e.g., 2-3 train, 1-2 test), chosen to keep total download size manageable — exact per-scenario file sizes beyond the one example fetched (Botnet-43/Neris, 35MB truncated pcap) were **not fetched for the other 12 scenarios in this pass** and should be checked before committing to a specific subset.
2. **Fallback if (1) proves too slow to download**: time-aware split *within* a single long scenario (e.g., first 70% of the capture's wall-clock time for train, last 30% for test) — weaker than scenario-level (adjacent-in-time windows can be more correlated than fully independent captures), but still strictly better than a random shuffle, and consistent with the "prefer time-aware over random" fallback the master prompt allows (§2.4) when scenario-level isn't available. If used, this must be documented as a **weaker generalization test** than the synthetic-dataset results, not silently presented as equivalent.

Either way: **the synthetic-dataset train/test split and its F1≈0.823 baseline result must not be touched** — a real-dataset experiment gets its own `dataset_version` in the experiment manifest (e.g. `"ctu13-v1-<scenario-ids>"`) and its own artifacts directory, never overwriting `artifacts/baseline/` or `artifacts/world_model/`.

---

## 6. Feature mapping (CTU-13 → PREVAIL's 59 features)

Per §0, PREVAIL recomputes all 59 features from packet-level rows using its *existing* code — so this is really a mapping from "raw pcap header fields" to `PacketEvent`, after which `features/flow.py`, `features/packet.py`, `features/temporal.py` run completely unchanged.

| `PacketEvent` field | Source in CTU-13 truncated PCAP | Confidence |
|---|---|---|
| `timestamp` | Packet capture timestamp (pcap header) | Direct — always present |
| `src_ip`, `dst_ip` | IP header | Direct |
| `src_port`, `dst_port` | TCP/UDP header | Direct (TCP/UDP only; ICMP has no ports — needs a documented convention, e.g. 0, matching how the synthetic generator already handles ICMP) |
| `protocol` | IP header protocol field | Direct |
| `tcp_syn/ack/fin/rst/psh/urg` | TCP header flags | Direct, TCP only |
| `ttl` | IP header | Direct — **not independently confirmed intact post-truncation in this pass**, needs verification |
| `tcp_window` | TCP header | Direct — same caveat as `ttl` |
| `fragmented` | IP header flags/fragment-offset | Direct, but expect **near-constant `False`** in modern-ish TCP traffic (IP fragmentation is rare when PMTU discovery works) — a real, low-variance feature for this dataset, not missing, just uninformative most of the time |
| `payload_size` | IP total-length header field minus header lengths | Direct if the total-length header field survives truncation (expected, per Stratosphere's own claim that headers are intact) — **not independently verified** |
| `retransmission` | **Not a native field — requires new derivation**: duplicate/out-of-order TCP sequence number detected within a flow | **New logic needed**, does not exist in the current adapter-agnostic code (the synthetic generator assigns this synthetically; a real adapter needs an actual duplicate-seq detector) |
| `attack_stage` | **Not per-packet** — must be joined from the separately-provided labeled bidirectional netflow file by matching flow 5-tuple + time window, then propagated to that flow's packets | New join logic; see leakage risk in §4. Only supports `benign` / `command_and_control` per §2 — `recon`/`initial_access`/`lateral_movement` are **UNAVAILABLE**, and any window containing only generic `Botnet` (non-C&C) traffic should be labeled with a distinct catch-all (e.g., a new, explicitly-scoped `bot_active_unclassified` bucket, or conservatively folded into `command_and_control` only where the netflow label literally says so) — **not** silently mapped onto one of the three unsupported synthetic stages. |

Given this, all 59 `flow__*`/`packet__*`/`temporal__*` features are **structurally derivable** — this dataset is not missing any feature family the way a flow-CSV-only dataset would force `packet_features` to null out entirely (data-contract.md §5's nullability rule). The real gaps are the **new adapter code** (PCAP parsing, retransmission detection, label-join) and the **attack-stage vocabulary reduction** (§2), not missing raw signal.

**Expected missingness**: none structurally, but empirically some features may turn out low-variance/uninformative on real traffic in ways the synthetic generator's deliberately-designed signatures don't exhibit (e.g., `fragmentation_ratio` likely near-zero throughout; `port_scan_score`'s heuristic threshold, tuned implicitly against the synthetic generator's scan behavior, may need recalibration against real scanning behavior if any exists in the chosen scenario — CTU-13 scenarios are botnet-behavior captures, not necessarily scan-heavy, so `recon`-like signal may simply be rare or absent in the data, consistent with `recon` being unavailable as a label too).

---

## 7. Reporting discipline for real-dataset results

Per instruction: **never combine synthetic and real metrics into one score.** Concretely:

- New experiment config/manifest namespace, e.g. `dataset_version: "ctu13-v1-<scenarios>"`, written to `artifacts/evaluation/real_dataset/` (new directory), never overwriting `artifacts/baseline/manifest.json` or `artifacts/world_model/manifest.json` (the existing synthetic-track manifests).
- `docs/experiments/*.md` gets either new files (`docs/experiments/real-dataset-baseline.md`, etc.) or clearly-separated sections — not merged tables with the synthetic numbers.
- `README.md` and `docs/limitations.md` get an explicit **"Synthetic validation" vs. "Real-dataset validation"** heading split once real results exist, per instruction.
- If real-dataset performance is substantially worse than synthetic (plausible, even likely, given real traffic's messier statistics and the reduced/harder-evidenced label set), the instruction is explicit: **report it and investigate, do not tune until it looks good.** This matches the project's existing pattern (D-005, D-008, D-010 in `DECISIONS.md` are all "found something concerning, investigated and documented it honestly" rather than silently fixed-until-flattering) and should be continued here.

---

## 8. Proposed integration plan (outline only — not implemented in this pass)

1. **Verify feasibility first, cheaply**: download just the one confirmed-small file (`botnet-capture-20110811-neris.pcap`, 35MB, scenario "Botnet-43") and inspect it with a lightweight tool (`scapy`, already a reasonable dependency to add) to confirm TTL/TCP-window/payload-length survive truncation, before committing to a larger multi-scenario download. This directly resolves the "not independently verified" flags in §3 and §6.
2. **New module**: `ingestion/pcap.py` (or similar) — parses a pcap into a `PacketEvent`-shaped DataFrame, matching `synthetic.py`'s `PACKET_COLUMNS` output shape exactly, so it plugs into `preprocessing/clean.py::load_packets`/`clean_packets` and `states/builder.py::build_states` unchanged. New dependency: a pcap-parsing library (`scapy` or `dpkt` — a build/threat-model note: this is new attack surface parsing untrusted binary input, so `threat-model.md`'s "Unsafe file parsing" row moves from "not yet applicable" to actually relevant, and should get real hardening, not just the CSV-only checks that exist today).
3. **New module**: a label-join step attaching `attack_stage` per packet from the labeled bidirectional netflow file, implementing the `benign`/`command_and_control`/unavailable-others policy from §2 and §6 explicitly (not inferred stage labels).
4. **New logic**: retransmission detection (duplicate/out-of-order TCP sequence numbers per flow).
5. **New tests**: label-join correctness (a known flow's packets get the right label), no-leakage property test extended to cover the PCAP path, a regression test pinning the parsed packet count/schema for the specific scenario file used (so a future re-download or library upgrade can't silently change results unnoticed).
6. **New scenario metadata**: since CTU-13 doesn't ship a `scenario_meta.csv` like the synthetic generator's own, one must be authored (scenario_id, which capture, has_attack, duration, stage vocabulary caveat) to feed `scenario_train_test_split` unchanged.
7. **Run the existing scripts against the new data source**: `run_pipeline.py`-equivalent, `train_baseline.py`, `train_world_model.py`, `evaluate_rollout.py`, `explain_demo.py`, `train_attack_stage.py` (with the reduced stage vocabulary) — all of these should need only a different input path / `dataset_version` string, not logic changes, if steps 2-6 are done correctly. This is the explicit test of whether "the ingestion layer already accepts... so swapping in a real dataset later does not require re-architecting" (README.md's existing claim) actually holds.
8. **Do not touch** `world_model/model.py`'s architecture unless step 7's results reveal a concrete, evidenced reason to (per instruction) — e.g., if one-step prediction on real data is dramatically worse in a way traceable to an architectural assumption (not just "real data is harder"), that would be a new `DECISIONS.md` entry with evidence, not a silent change.

**Explicitly out of scope for this document**: actually writing any of the above code. The user asked to review this research and the dataset choice before implementation begins.

---

## 9. Phase 1 verification findings — two assumptions from §1-§8 were wrong

Verified directly against the authoritative source (`stratosphereips.org`, and the actual `mcfp.felk.cvut.cz` directory listings/READMEs for scenarios 42, 43, and 54 — fetched live, not from memory or a secondary source) before any adapter code was written, per instruction.

### 9.1 WRONG: "the 35MB per-scenario pcap is the scenario's data"

The first-pass document (§3.2, §6) treated `botnet-capture-<date>-<malware>.pcap` (~35-109MB depending on scenario) as if it were usable as *the* scenario capture. **This is wrong.** The scenario 42 and 43 READMEs state explicitly and unambiguously: this file "contains only the botnet traffic," captured "on the interface of the virtual machine being infected," and it **excludes background and normal network activity** entirely. There is a *separate*, much larger file — `capture<date>.truncated.pcap.bz2` — which is the actual complete, all-hosts capture (with payloads truncated for privacy, headers intact), and it is THIS file, not the small one, that would be needed to get both benign and attack traffic for PREVAIL's baseline/World-Model comparison (which needs benign windows to measure FPR against, not just attack windows).

Verified sizes for the large full-traffic file, fetched directly from 3 of the 13 scenario directories:

| Scenario | Malware | Small (attack-only) pcap | Large (full-traffic) truncated pcap |
|---|---|---|---|
| 42 | Neris (2011-08-10) | 56M | **1.2G** |
| 43 | Neris (2011-08-11) | 35M | **1.1G** |
| 54 | Fast-flux (2011-08-15) | 109M | **843M** |

(The other 10 scenarios' large-file sizes were not confirmed — repeated fetch attempts to their directories failed during this pass, see §10. Based on these 3 confirmed data points, ranging 843M-1.2G, there is no reason to expect any of the remaining 10 are dramatically smaller — CTU-13 scenario captures generally run 1-15+ hours.)

**Corrected §6 feature-mapping implication**: the mapping table in §6 still holds (all fields are derivable from the *headers* the truncation preserves), but only when read against the **large** truncated file, not the small one. Using only the small file, as the first pass implicitly assumed feasible, would produce an attack-only dataset with zero benign windows — unusable for the baseline/FPR/World-Model comparison this integration exists to produce.

### 9.2 WRONG: "bidirectional NetFlow, 4 flat label categories"

The first pass (§1 table, §2) stated CTU-13 uses bidirectional NetFlow with exactly 4 flat categories (`Background/Normal/Botnet/C&C`). The scenario-level READMEs (42, 43) say the primary labeled file (`capture<date>.pcap.netflow.labeled`) is **unidirectional** Argus, and the actual label values are compound strings, not 4 flat categories — confirmed naming patterns include `From-Botnet`, `To-Botnet` (traffic *to* an infected host from an unknown/not-necessarily-malicious source), `From-Normal`, `To-Normal` (unsolicited inbound to a normal host), plus `Background` and `LEGITIMATE`. This is a richer, more specific label space than "4 categories," though it is still **not** a multi-stage kill-chain label — §2's core conclusion (no native recon/initial-access/lateral-movement evidence) is unchanged and independently re-confirmed by this closer reading.

**Not fully resolved**: the general Stratosphere overview page (fetched in the first pass) separately mentions "bidirectional NetFlows... much more detailed labels" as an available format, and the scenario 42/43 directory listings do show a `detailed-bidirectional-flow-labels/` subdirectory and a `capture<date>.binetflow.2format` file (424-664M) that were not opened/inspected in this pass. It's possible a bidirectional-labeled alternative exists per scenario and would be preferable for the label-join step (Phase 5 of the approved plan) if it avoids matching each direction of a flow separately. **Flagged as unresolved, not resolved by assumption** — would need to be checked before writing the label-join code, if this integration proceeds.

---

## 10. Feasibility blocker: this environment cannot reliably download the required file size

This is the assumption that most needed direct testing, and it failed. Summary of what was actually tested (2026-09-20, this session):

- **Connection reliability to `mcfp.felk.cvut.cz` (147.32.82.194) from this sandbox's direct network egress**: across repeated `curl` attempts (HEAD requests and real download attempts), the TCP/TLS connection succeeded only intermittently — roughly 1 in 3 attempts connected at all; the rest failed immediately with "couldn't connect to server" (curl exit 7) or timed out during the TLS handshake. General internet connectivity was independently confirmed working in the same session (`pypi.org`, `cvut.cz` root domain both responded normally), so this is specific to this host, not a blanket sandbox network failure.
- **Sustained transfer rate, the one time a connection succeeded**: a real download attempt against the *smallest confirmed file* (scenario 54's attack-only pcap, 109MB) sustained only **~17 KB/s** over a 30-second sampled window (503,943 bytes transferred).
- **Extrapolated time cost**: at ~17 KB/s, the 109MB attack-only file alone would take **~108 minutes**; the actually-required 843MB-1.2GB full-traffic file would take **14-20+ hours** — and given the ~65% per-attempt connection failure rate observed, a multi-hour *unbroken* transfer is very unlikely to complete without a resumed-download retry loop across many failures, which was not attempted given the scale of the problem this reveals.
- **Context**: this session separately struggled to reliably download a single ~200-280MB PyTorch wheel from `download.pytorch.org` (Milestone 12, Docker build) — multiple attempts, one outright timeout, eventual success only after ~20-40 minutes of real wall-clock time with retries. The CTU-13 full-traffic file is 4-6x larger than that already-difficult download, on a host with a substantially worse (not just slower, but less *reliable*) connection than PyTorch's CDN.
- **Mirror search**: Kaggle hosts several CTU-13 mirrors, but they distribute pre-extracted flow CSV/parquet, not raw PCAP — the wrong shape for PREVAIL's packet-level ingestion contract (§0) — and at least one is explicitly described in independent commentary as covering only "a tiny time window" and "useless for ML." No Academic Torrents or Zenodo mirror was found. No better-positioned alternative source was identified in this pass.

**This meets the explicit stop condition from the approved implementation plan**: *"CTU-13 cannot be obtained/accessed as expected."* Per instruction: reporting this rather than proceeding, hiding it, or fabricating a result.

---

## 11. What this does and doesn't rule out

- **Does not invalidate the dataset choice itself.** CTU-13 remains the best-reasoned candidate on scientific grounds (§2-§3) — the problem is this environment's ability to *obtain* it right now, not a flaw in the recommendation.
- **Does rule out, for now**: any integration path that requires the large (843MB-1.2GB+) full-traffic truncated pcap for any of the 3 confirmed scenarios, downloaded from this sandbox's current network path, in a single session.
- **Options for how to proceed** (not decided in this document — for the user to choose):
  1. **Retry later / different network**: the connection instability may be transient (server load, routing) rather than permanent; a retry at a different time, or a download performed from an environment with a better path to `mcfp.felk.cvut.cz`, may simply work.
  2. **Scoped-down partial integration**: use only the small attack-only pcaps (36-109MB, confirmed feasible in principle) to validate the *packet-parsing and feature-extraction* side of the adapter end-to-end (Phases 2-4 of the approved plan) against real attack traffic, while being explicit that **no benign-class real-data results (baseline FPR, benign/attack discrimination) can be produced this way** — the integration would validate "does PREVAIL's pipeline run correctly on real packets" without validating "does it distinguish real attacks from real benign traffic," which is a materially smaller (but honestly scoped) deliverable, not the full plan as approved.
  3. **Find/negotiate a different access path**: e.g. attempt the `detailed-bidirectional-flow-labels/`/`binetflow.2format` files (424-664MB, still large but smaller than the full pcap, though these are flow-level not packet-level and would require raw-pcap regardless — this doesn't actually resolve the packet-level requirement, listed for completeness not as a real alternative).
  4. **Defer real-dataset integration entirely** and keep the synthetic-validation track as the documented, honestly-labeled deliverable, revisiting this when a more reliable path to a real dataset exists.
- **Not chosen unilaterally**: per the approved plan's own stop-condition instruction ("do not hide these issues"), this document stops here and reports back rather than picking one of the above without the user's input.
