# PREVAIL — Open Questions

Date: 2026-09-20

Tracked here rather than silently resolved, per master prompt rule 0.6.

## OQ-1: Primary source PDF missing

`/mnt/data/bugbounty guide.pdf`, named by the master prompt as the primary project reference,
does not exist in this environment (`ls /mnt/data` → No such file or directory). **Status:
unresolved.** If the user/team has this file, it should be placed at a known path (e.g.
`docs/research/source-material/bugbounty-guide.pdf`) and this research pass's conclusions
re-checked against it — in particular `source-requirements.md`, which currently relies on
secondary (GitHub repo) confirmation of the PS text rather than the primary document.

**Impact if never resolved:** Low-to-medium. Four independent SIH26153 submissions converge on
the same PS identity and core mandate, which is reasonably strong secondary evidence. But the
literal PDF might contain non-functional constraints, deliverable formats, or scoring criteria
not visible in competitor repos (which reflect what teams *chose* to build, not necessarily
everything the PS *asked for*).

## OQ-2: No telemetry dataset bundled in this environment

No PCAP file, NetFlow export, or labeled CSV dataset exists anywhere under `/home/gokulraj/sih`
or `/mnt/data`. The master prompt assumes a dataset is either provided or will be
acquired. Competitor repos use CTU-13, CSE-CIC-IDS2018, CIC-IDS-2017, UNSW-NB15, or CICIoT2023 —
all real, standard, publicly documented network-security datasets, but none are pre-downloaded
here (some run to multiple GB and may require registration or slow download).

**Status update (2026-09-20, post-build):** (b) was done — the synthetic validation dataset and
full pipeline exist and are documented throughout `docs/experiments/`. (a) was then attempted
twice: a research-only pass recommended CTU-13 (`docs/research/real-dataset-integration.md`
§1-§8), and a follow-up Phase 1 verification pass found two of that pass's assumptions were wrong
and, more consequentially, a **hard download-feasibility blocker**: the actually-required CTU-13
file (843MB-1.2GB full-traffic truncated pcap; the small ~35-109MB pcap turned out to be
attack-traffic-only) could not be reliably downloaded from this environment's network — ~65%
per-attempt connection failure and ~17 KB/s sustained transfer when it did connect, extrapolating
to 14-20+ hours with a high chance of failing mid-transfer. See `docs/research/
real-dataset-integration.md` §9-§11 and `DECISIONS.md` D-012 for full detail. **This remains the
single most consequential open item in the repo** — not for lack of a plan, but for lack of a
reliable way to obtain the data in this environment. Options recorded for a future session/user
decision: retry later or from a different network, a scoped-down attack-only-pcap partial
validation (no benign-class real results), pursuing an alternative file/format on the same host,
or continuing to defer.

**Do not report evaluation metrics from a synthetic dataset as if they were results on real
attack telemetry** — any synthetic-data results must be labeled "pipeline validation on
synthetic data" throughout all docs, dashboards, and reports, never presented as PS-evidence of
detection/forecasting performance.

## OQ-3: PS literal text not directly extracted

The SIH 2026 master-catalogue PDF (`sih-2026-problem-statements.shaikrohit187.workers.dev`) could
not be parsed to text by the fetch tool (returned raw PDF object structure). The
`codehuntersacademy.com/sih-2026-ps` explorer page also did not surface PS 26153's text in a
static fetch (it's likely a JS-rendered filter/search UI). **Status: unresolved** — a follow-up
pass with a tool capable of PDF text extraction (or a headless-browser fetch of the JS-rendered
explorer) could resolve this. Until then, `source-requirements.md` is built on convergent
secondary evidence (4 independent repos), explicitly flagged as such, not presented as a literal
PS quotation.

## OQ-4: Un-inspected SIH26153-adjacent repos

Search surfaced additional repos not fetched in this pass due to time-boxing:
`MADOUT20/SIH-2026`, `Abhrxdip/attack_forecasting`, `Prasad14-cyber/network_attack_forecasting`,
`chandanbodugam-max/CYBERWORLD--Network-Traffic-Analysis`. **Status: open.** Recommend a
follow-up research pass inspects these before the differentiation claims in
`differentiation.md` are treated as final/locked, in case one of them also implements a what-if
simulator (which would remove PREVAIL's current primary differentiator).

## OQ-5: Suspiciously strong self-reported competitor metrics

`Kshitiz-Khandelwal/AI-Based-Forecasting-SIH2026` reports 0 false positives across evaluation and
99.94% F1 on an exfiltration stage, plus a 9-microservice production architecture, for what
appears to be a hackathon submission repo. **Status: not independently verifiable** — the repo
was not cloned/run, only its README was read. Recorded as "self-reported, not reproduced" in
`prior-art.md`. Do not use these numbers as a target PREVAIL must beat; they may reflect
train/test leakage, cherry-picked splits, or simply optimistic reporting — this cannot be
determined without running the code.

## OQ-6: Attack-stage taxonomy disagreement across competitors

Competitor repos use 5-stage and 7-stage kill-chain taxonomies with different orderings (one
places Lateral Movement before C2, another after; stage counts differ). Master prompt §10 already
anticipates this by requiring a three-layer mapping (dataset-native label → normalized behaviour
→ ATT&CK tactic/technique) rather than one fixed taxonomy — no action needed beyond following
that existing instruction, but flagged here so the team doesn't assume there's an industry-
standard stage list to simply adopt.
