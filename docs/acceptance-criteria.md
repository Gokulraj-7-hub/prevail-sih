# PREVAIL — Acceptance Criteria Status

Tracks master prompt §36 literally. Updated 2026-09-20, single continuous autonomous build session. Marked `[x]` only when actually done and verified in this repo; `[~]` for partial/honestly-scoped; `[ ]` for not started.

## Research

- [x] SIH PS requirements extracted — `docs/research/source-requirements.md` (secondary-source confirmed across 4 independent repos; primary PDF was never available in this environment, see OQ-1)
- [x] prior-art research complete — `docs/research/prior-art.md`, 11 cited rows
- [x] previous SIH projects reviewed — 4 SIH26153-specific repos inspected directly; 4 more found but not fetched (OQ-4, time-boxed)
- [x] differentiation documented — `docs/research/differentiation.md`

## Data

- [x] dataset ingestion works — synthetic packet-event CSV path, tested; real-PCAP/binary ingestion not implemented (see threat-model.md note)
- [x] feature pipeline reproducible — deterministic, seeded, tested (`tests/property/test_windowing.py`)
- [x] temporal windows validated — property tests: ordering, contiguity, no future leakage
- [x] leakage checks pass — scenario-level split enforced + property-tested, pipeline hard-fails on overlap
- [x] attack-stage mappings documented — `configs/features/attack_stage_mapping.yaml`, confidence-scored

## ML

- [x] Logistic Regression baseline — `docs/experiments/baseline.md`
- [x] World Model V1 — `docs/experiments/world-model.md`
- [x] one-step prediction — same doc, real metrics
- [x] K-step rollout — `docs/experiments/k-step.md`, K∈{1,2,3,5} all reported
- [x] future attack probability — `attack_stage/interpret.py`, demoed in `docs/experiments/attack-stage.md`
- [x] ATT&CK mapping — versioned, confidence-scored, applied live via API
- [x] explainability — SHAP + temporal occlusion, `docs/experiments/explainability.md`

## Innovation

- [x] what-if intervention simulator — implemented, API-wired, frontend-wired
- [x] baseline vs intervention comparison — `docs/experiments/intervention.md`
- [x] limitations documented — including the honest negative result (D-010) that both tested interventions increased forecast P(attack)

## Evaluation

- [x] Precision — every classification result
- [x] Recall — every classification result
- [x] F1 — every classification result
- [x] False Positive Rate — every classification result
- [x] temporal evaluation — K-step error accumulation
- [x] ablation study — Experiments E/F/G (feature family); H/I (window size, sequence length) explicitly NOT run, documented as such
- [~] generalization analysis — `docs/experiments/generalization.md`: scenario-safe splitting is structural to every experiment; dedicated cross-attack-type holdout and cross-dataset validation NOT run (blocked on a second dataset)

## Product

- [x] FastAPI — 10 endpoints, live-tested with curl and pytest
- [x] frontend — Next.js dashboard, 7 tabs, live-tested with Playwright against the real API
- [x] offline operation — static code verification (no outbound calls anywhere) AND a live `docker compose` smoke test (health -> load telemetry -> forecast -> dashboard render, all passing) done; the one remaining gap is a true network-egress-*blocked* runtime test, which was environment-limited (no host firewall admin) — see `docs/architecture/offline-verification.md`
- [x] Docker — `Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`; built and live-tested end-to-end, including catching and fixing a real undeclared-dependency bug (`pyarrow`, DECISIONS.md D-011) that only surfaced in the from-scratch container build
- [~] security testing — threat-model checklist mostly verified (static checks + unit tests), some items explicitly still Planned (auth layer, CSP header, dependency-audit automation) — see `docs/architecture/threat-model.md`
- [x] automated tests — unit/integration/property, 21 tests passing (`.venv/bin/python -m pytest tests/ -q`)

## SIH

- [x] architecture diagram — `docs/architecture/architecture-diagram.svg`, embedded in `architecture.md`
- [x] results charts — `scripts/generate_result_charts.py` renders 5 charts directly from the real `artifacts/*.json`/`manifest.json` data (no new numbers, just visualized), embedded in the relevant `docs/experiments/*.md`
- [x] demo dataset — the synthetic dataset, `data/raw/synthetic_packets.csv`, baked into the Docker image
- [x] 2-minute demo flow — `docs/demo/demo-script.md`
- [ ] presentation material (slide deck) — not produced this pass; the diagram, charts, and demo script it would be built from all exist
- [~] technical report — this repository's `docs/` tree functions as one (24 markdown docs, all cross-linked), but no single consolidated PDF/deck-style report document has been assembled

## Honest summary

Every research, data, ML, innovation, evaluation, and core-product checkbox is genuinely done and verified against real (synthetic) results in this repo, including a fully working, live-tested Docker deployment. The gaps are: (1) real-dataset integration — the single most consequential remaining item, tracked everywhere as the top open question; (2) a formal slide deck for live SIH presentation (the demo script, architecture diagram, and result charts that would feed one all exist, just not assembled into slides); (3) a few security-hardening items correctly scoped as "Planned" rather than falsely marked done (auth layer, CSP, dependency-audit automation, subprocess-isolated binary PCAP parsing).
