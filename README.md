# PREVAIL — Predictive Network Attack Trajectory & Intervention Learning

SIH26153 (NTRO, Blockchain & Cybersecurity theme): *"AI based Network Attack Forecasting from Network Traffic Data"* — see `docs/research/source-requirements.md`.

## The problem

Most network defense tools answer one question: **is this traffic malicious, right now?** PREVAIL exists because that question is not enough. A static classifier treats every flow as an independent sample and tells you about the present. It cannot tell you what an attacker is likely to do *next* — and by the time a classifier fires on a completed intrusion stage, the defensive window to act on that stage has often already closed.

PREVAIL instead learns `P(S_{t+1} | S_t)` — a **temporal World Model** over network state sequences — and rolls it forward K steps to forecast attack progression: `S_t → Ŝ_{t+1} → Ŝ_{t+2} → ... → Ŝ_{t+K}`. It is **not** `PCAP → classifier → attack/benign`; that reduction would miss the entire point of the PS (see master prompt §1).

## World Model concept

```text
Historical network states (5s windows, flow+packet+temporal features)
      -> Temporal Transformer encoder (causal, small: 3 layers, 4 heads)
      -> next-state prediction (regression head)
      -> K-step autoregressive rollout
      -> attack-stage interpretation layer (independent classifier)
      -> MITRE ATT&CK mapping (versioned, hand-authored, confidence-scored)
      -> explainability (SHAP feature attribution + temporal window evidence)
      -> [proposed extension] defensive what-if intervention simulator
```

Every one of these stages is real, implemented, and tested against a dataset — see `docs/experiments/*.md` for actual results, not aspirational descriptions.

## Architecture

See `docs/architecture/architecture.md` (module map), `docs/architecture/data-contract.md` (the `NetworkState` schema and 59-feature registry), and `docs/architecture/intervention-model.md` (the what-if simulator).

```text
sih/
├── docs/            research, requirements, architecture, experiments, demo, limitations
├── configs/         feature registry, ATT&CK mapping (versioned YAML)
├── data/            raw / interim / processed / metadata
├── src/prevail/     production package (ingestion -> ... -> api)
├── scripts/         pipeline / training / eval / demo entry points
├── tests/           unit, integration, property
├── frontend/        Next.js + TypeScript dashboard
├── artifacts/        trained models, experiment manifests, reports
├── Dockerfile, frontend/Dockerfile, docker-compose.yml
```

## Datasets — read this before trusting any number in this repo

**Every result currently in this repository is on a synthetic validation dataset** (`prevail.ingestion.synthetic`), not a real-world capture. This was a deliberate, documented choice (`DECISIONS.md` D-003): no real PCAP/flow dataset was bundled in the build environment, and downloading a multi-GB benchmark (CICIDS2017/2018, CTU-13) before proving the pipeline architecture was scientifically valid would have inverted the master prompt's own "simplest scientifically valid version first" principle. Real-dataset integration is the top tracked open item (`docs/research/open-questions.md` OQ-2) — the ingestion layer already accepts flow-CSV format compatible with real exports, so swapping in a real dataset does not require re-architecting.

**Do not quote any metric in this repo as evidence of real-world detection/forecasting performance.** Every doc under `docs/experiments/` says so explicitly and repeats it in-line next to every table.

## Training / running the pipeline

```bash
make setup                                    # venv + deps
.venv/bin/python scripts/generate_synthetic_dataset.py
.venv/bin/python scripts/run_pipeline.py       # ingestion -> states -> sequences -> leakage checks
.venv/bin/python scripts/train_baseline.py     # Experiment A: Logistic Regression
.venv/bin/python scripts/train_world_model.py  # Experiment C: World Model V1, one-step
.venv/bin/python scripts/evaluate_rollout.py   # Experiment D: K-step rollout
.venv/bin/python scripts/train_attack_stage.py # attack-stage classifier + ATT&CK demo
.venv/bin/python scripts/explain_demo.py       # explainability demo
.venv/bin/python scripts/intervention_demo.py  # what-if simulator demo
.venv/bin/python scripts/ablation_features.py  # Experiments E/F/G
.venv/bin/python -m pytest tests/ -q           # full test suite
```

## Running the product

```bash
docker compose up --build
# API:       http://localhost:8000/api/v1/health
# Dashboard: http://localhost:3000
```

or without Docker:

```bash
make api          # FastAPI on :8000
cd frontend && npm install && npm run dev   # Next.js on :3000
```

## Evaluation (synthetic validation data — see caveat above)

| Experiment | Headline result |
|---|---|
| A — Logistic Regression baseline | Test F1 0.823, ROC-AUC 0.870, FPR 0.050 (`docs/experiments/baseline.md`) |
| C — World Model V1, one-step | Normalized MSE 0.369, cosine similarity 0.714 (`docs/experiments/world-model.md`) |
| D — K-step rollout (K=1,2,3,5) | Error accumulates gracefully: normalized MSE 0.376→0.769, F1 0.877→0.711, FPR stays flat ~0.02-0.035 (`docs/experiments/k-step.md`) |
| Attack-stage + ATT&CK | 97.5% overall stage accuracy; honestly weak on rare classes (C2 recall 0.10, 10 test samples) (`docs/experiments/attack-stage.md`) |
| E/F/G — feature ablation | Packet-only features (13) nearly match all 59 combined; flow-only underperforms everything, 3x the FPR (`docs/experiments/ablation.md`) |
| K — what-if intervention | Mechanism works; **both tested interventions increased forecast P(attack) instead of decreasing it** — an honest, investigated, documented limitation, not a flattering demo (`docs/experiments/intervention.md`) |

## Offline operation

`docker compose up --build` + `scripts/offline_smoke_test.sh` passes end-to-end (health → load demo telemetry → forecast → dashboard render), and static code verification confirms zero outbound network calls anywhere in the inference path. This process caught and fixed a real bug: an undeclared `pyarrow` dependency that only surfaced in a from-scratch container build, not in local dev (see `DECISIONS.md` D-011). A true network-*egress-blocked* runtime test was environment-limited (no host firewall admin in this sandbox) — see `docs/architecture/offline-verification.md` for exactly what is and isn't verified.

## Limitations

**Read `docs/limitations.md` before any demo or presentation.** It exists specifically so nothing here gets oversold.

## Research & decision trail

- `docs/research/` — prior-art research, differentiation strategy, open questions, research log.
- `DECISIONS.md` — every non-obvious architectural choice, with context/alternatives/evidence/reason/trade-offs, including two real bugs found and fixed mid-build (D-005 labeling, D-008 metric units) and one real negative result investigated in depth (D-010, the what-if simulator).
