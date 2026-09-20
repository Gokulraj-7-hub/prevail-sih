# SIH26153 — PREVAIL
## Complete Research-to-Build Master Prompt for Claude Code

You are the lead research engineer and implementation agent for SIH26153.

Project name: **PREVAIL — Predictive Network Attack Trajectory & Intervention Learning**

Your job is to take this project from **problem-statement research → prior-art research → requirements → architecture → dataset engineering → baseline → temporal world model → K-step forecasting → ATT&CK mapping → explainability → defensive what-if simulation → offline deployment → evaluation → documentation → SIH demo**.

Do not jump directly into coding. Research and validate the design first.

---

# 0. PRIMARY SOURCE AND NON-NEGOTIABLE RULE

The uploaded file:

`/mnt/data/bugbounty guide.pdf`

is the primary project reference available to you. Also use the SIH26153 problem statement supplied to the project as the authoritative statement of required functionality.

Before making architectural decisions:

1. Read and inspect the relevant source material.
2. Extract the exact SIH26153 requirements into a project requirements document.
3. Preserve the terminology used by the problem statement.
4. Do not silently change a mandatory requirement into a different problem.
5. If you add something that is not explicitly required, label it clearly as:
   **“Proposed innovation / extension beyond the mandatory PS requirement.”**
6. If the source material is ambiguous, record the ambiguity instead of inventing a requirement.
7. Never claim that a feature is novel merely because you did not find it during research.

The project must remain an **offline-capable temporal network attack forecasting / world-model system**, not merely a static IDS or attack classifier.

---

# 1. CORE PROBLEM TO SOLVE

The system must model how network states evolve over time and forecast future attack progression.

The conceptual requirement is:

`P(S_{t+1} | S_t)`

and then a K-step forward rollout:

`S_t → S_hat_{t+1} → S_hat_{t+2} → ... → S_hat_{t+K}`

The system should use temporal network telemetry rather than treating every flow as an independent sample.

The solution must cover the SIH requirements around:

- flow-level features
- packet-level features
- temporal state representation
- learned state-transition dynamics / World Model
- next-state prediction
- K-step forecasting
- future infiltration / attack progression probability
- attack-stage interpretation
- MITRE ATT&CK mapping
- explainability
- comparison against Logistic Regression
- Precision
- Recall
- F1
- False Positive Rate
- offline / air-gapped operation
- reproducible evaluation

Do not reduce the project to:

`PCAP → classifier → attack/benign`

That would miss the central World Model requirement.

---

# 2. PROJECT PHILOSOPHY

Follow these principles throughout development:

### 2.1 Evidence before implementation

Research first. Implement second.

### 2.2 Build the simplest scientifically valid version first

Do not start with a giant Transformer/GNN/LLM architecture.

First prove:

1. data is valid
2. temporal windows are valid
3. state representation is valid
4. baseline works
5. one-step prediction works
6. K-step rollout works
7. evaluation is trustworthy

Then add sophistication.

### 2.3 No fake novelty

Existing systems are not automatically a reason to reject the PS.

Instead determine:

- what existing systems already do
- how close they are
- which features they provide
- what they do not provide
- what the SIH PS specifically requires
- what PREVAIL can add without violating the PS

### 2.4 No benchmark leakage

Never randomly split adjacent temporal windows from the same attack scenario into train and test if that causes temporal or scenario leakage.

Prefer time-aware / scenario-aware evaluation.

Document every split decision.

### 2.5 No unsupported causal claims

The defensive intervention simulator is a model-based “what-if” scenario tool.

Do NOT claim:

“the intervention causally prevents the attack”

unless a proper causal methodology and experimental evidence support that claim.

Use language such as:

“the model forecasts a lower probability under the simulated intervention.”

---

# 3. PHASE 0 — RESEARCH THE SOURCE MATERIAL

Before coding, inspect:

- `/mnt/data/bugbounty guide.pdf`
- the SIH26153 problem statement
- any project files already present
- any existing repository structure
- any previous research notes

Create:

`docs/research/source-requirements.md`

Include:

## 3.1 Exact problem requirements

Create a table:

| Requirement | Mandatory? | Source | Implementation plan | Validation |
|---|---|---|---|---|

Every requirement must have a validation method.

## 3.2 Terminology

Define and preserve:

- network state
- temporal state
- state transition
- World Model
- K-step rollout
- infiltration state
- attack trajectory
- explainability
- packet-level feature
- flow-level feature

Do not redefine these casually.

## 3.3 Unknowns

Create:

`docs/research/open-questions.md`

Track unresolved issues rather than silently guessing.

---

# 4. PHASE 1 — DEEP PRIOR-ART / EXISTING-SOLUTION RESEARCH

This phase is mandatory.

Search broadly across:

- GitHub
- Google Scholar
- IEEE
- ACM
- arXiv
- NIST
- MITRE ATT&CK
- vendor documentation
- security research blogs
- existing SIH projects
- public demos
- relevant datasets
- relevant open-source implementations

Search concepts such as:

- network attack forecasting
- temporal intrusion prediction
- cyber attack trajectory prediction
- network world model
- temporal world model cybersecurity
- multi-step attack forecasting
- attack state transition model
- cyber counterfactual simulation
- defensive intervention simulation
- future attack state prediction
- temporal Transformer intrusion detection
- GRU attack forecasting
- network state transition prediction
- MITRE ATT&CK forecasting

Also inspect previously found public implementations of SIH26153, including the repositories/projects identified during the team's prior research.

IMPORTANT:
Do not copy their code.

Use them as:

- feature references
- architecture references
- evaluation references
- UI references
- missing-feature references
- baseline references

Record all useful observations.

Create:

`docs/research/prior-art.md`

For each relevant solution:

| Project/Paper | URL | Core approach | Features | Model | Forecasting? | K-step? | ATT&CK? | Explainability? | Intervention? | Gap vs PREVAIL |
|---|---|---|---|---|---|---|---|---|---|---|

---

# 5. PHASE 2 — DIFFERENTIATION STRATEGY

Do not claim PREVAIL is novel simply because it has a dashboard.

Develop a defensible differentiation.

The proposed direction is:

## Required core

Temporal network World Model:

`historical states → learned transition dynamics → future states`

## Proposed extension

### Attack Trajectory Simulator

Compare:

`Baseline forecast`

versus

`Forecast under simulated defensive intervention`

Example:

WITHOUT INTERVENTION:

`Initial Access → Lateral Movement → C2`

WITH SIMULATED HOST ISOLATION:

`Initial Access → reduced Lateral Movement probability → reduced C2 probability`

This is an extension, not a replacement for the SIH requirement.

Potential intervention examples:

- isolate host
- block destination port
- block suspicious source
- disable suspicious communication edge
- segment a network path
- remove a suspicious asset from the simulated state

Only support interventions that can be represented honestly in the state representation.

Create:

`docs/research/differentiation.md`

Include:

- what prior work already does
- what PREVAIL does differently
- what is merely implementation detail
- what is actually an architectural contribution
- limitations
- claims we must NOT make

---

# 6. PHASE 3 — REQUIREMENTS SPECIFICATION

Create:

`docs/requirements/SRS.md`

Functional requirements:

### FR-01
Import supported telemetry / datasets.

### FR-02
Extract flow-level features.

### FR-03
Extract packet-level features where source data permits.

### FR-04
Construct temporal windows.

### FR-05
Construct network states.

### FR-06
Construct chronological state sequences.

### FR-07
Train Logistic Regression baseline.

### FR-08
Train World Model.

### FR-09
Predict next network state.

### FR-10
Perform K-step forward rollout.

### FR-11
Estimate future attack/infiltration probability.

### FR-12
Map forecast behaviour to attack stages.

### FR-13
Map relevant behaviour to MITRE ATT&CK.

### FR-14
Provide evidence-based explainability.

### FR-15
Evaluate against baseline.

### FR-16
Provide offline operation.

### FR-17
Provide optional defensive what-if simulation.

Non-functional requirements:

- reproducibility
- offline capability
- deterministic preprocessing
- model versioning
- auditable experiments
- no hidden cloud dependency
- reasonable inference latency
- clear failure states
- safe handling of untrusted PCAPs

---

# 7. PHASE 4 — SYSTEM ARCHITECTURE

Use a modular architecture.

Recommended repository:

```text
prevail/
├── README.md
├── LICENSE
├── pyproject.toml
├── Makefile
├── docker-compose.yml
│
├── docs/
│   ├── research/
│   │   ├── source-requirements.md
│   │   ├── prior-art.md
│   │   ├── differentiation.md
│   │   └── open-questions.md
│   ├── requirements/
│   │   └── SRS.md
│   ├── architecture/
│   │   ├── architecture.md
│   │   ├── data-contract.md
│   │   └── threat-model.md
│   ├── experiments/
│   └── demo/
│
├── configs/
│   ├── datasets/
│   ├── features/
│   ├── models/
│   └── experiments/
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── metadata/
│
├── src/
│   └── prevail/
│       ├── ingestion/
│       ├── preprocessing/
│       ├── features/
│       ├── states/
│       ├── sequences/
│       ├── baselines/
│       ├── world_model/
│       ├── rollout/
│       ├── attack_stage/
│       ├── attack_mapping/
│       ├── explainability/
│       ├── intervention/
│       ├── evaluation/
│       ├── api/
│       └── common/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── property/
│   └── regression/
│
├── frontend/
│
├── scripts/
├── notebooks/
└── artifacts/
```

Keep research code separate from production code.

---

# 8. PHASE 5 — NETWORK STATE DATA CONTRACT

This is one of the most important design decisions.

Create:

`docs/architecture/data-contract.md`

Define:

```text
NetworkState
    timestamp
    window_start
    window_end
    flow_features
    packet_features
    temporal_features
    metadata
    attack_label (training/evaluation only)
    attack_stage (training/evaluation only)
```

Do not feed ground-truth labels into the predictive feature vector.

Example feature families:

## Flow-level

- source/destination IP statistics
- source/destination port statistics
- protocol distribution
- TCP flag ratios
- bytes
- packets
- flow duration
- inter-arrival time
- bidirectional traffic ratio
- connection counts
- failed connection counts

## Packet-level

Where raw packets are available:

- TTL
- TCP window
- fragmentation
- payload-size distribution
- retransmissions
- packet timing
- port access sequence characteristics

## Temporal / aggregate features

- flow rate
- packet rate
- new connection rate
- failed connection rate
- unique destination rate
- port entropy
- source entropy
- traffic burstiness
- change from previous window
- rolling mean
- rolling variance

Do not blindly add hundreds of features.

Every feature must have:

- name
- type
- unit
- source
- calculation
- missing-value strategy
- leakage risk
- justification

---

# 9. PHASE 6 — TEMPORAL WINDOWING

Start with:

**5-second windows**

but treat this as an experimental hyperparameter.

Also test:

- 5 seconds
- 10 seconds
- possibly 30 seconds depending on dataset

Do not assume one window size is universally correct.

Construct:

```text
W0 → S0
W1 → S1
W2 → S2
W3 → S3
...
```

Then sequences:

```text
[S0,S1,...,S9] → S10
```

Store window metadata.

Avoid overlapping train/test leakage.

---

# 10. PHASE 7 — ATTACK TIMELINE CONSTRUCTION

Create:

`src/prevail/attack_stage/`

Build a normalized stage vocabulary.

Do NOT force every dataset into a fake identical taxonomy.

Instead create:

1. dataset-native label
2. normalized behavioural category
3. optional MITRE ATT&CK mapping

Example:

```text
dataset label
      ↓
normalized behaviour
      ↓
ATT&CK tactic/technique
```

Maintain a mapping file:

`configs/features/attack_stage_mapping.yaml`

Every mapping must have:

- source
- confidence
- rationale
- review status

Do not claim an ATT&CK technique when the available evidence only supports a broad tactic.

---

# 11. PHASE 8 — DATA QUALITY

Before ML:

Run:

- missing-value report
- duplicate report
- timestamp integrity
- label distribution
- class imbalance
- feature distribution
- outlier analysis
- train/test contamination checks
- scenario overlap checks

Create:

`artifacts/data_quality_report.html`

Fail the pipeline if critical leakage is detected.

---

# 12. PHASE 9 — LOGISTIC REGRESSION BASELINE

Implement first.

Baseline input:

Current state / allowed historical aggregate features.

Baseline output:

Attack probability / required baseline target.

Metrics:

- Precision
- Recall
- F1
- False Positive Rate
- ROC-AUC where appropriate
- PR-AUC where class imbalance makes it useful

Keep the baseline reproducible.

Save:

- preprocessing
- coefficients
- metrics
- confusion matrix
- configuration
- random seed

This is required by the SIH PS.

---

# 13. PHASE 10 — WORLD MODEL V1

Start simple.

Recommended architecture:

```text
Historical states
      ↓
Feature projection
      ↓
Positional encoding
      ↓
Temporal Transformer Encoder
      ↓
Next-state prediction head
```

Input:

```text
(batch, sequence_length, feature_count)
```

Output:

```text
predicted next state
```

Do not begin with a massive model.

Start with a small Transformer.

Example initial experiment:

- sequence length: 10
- 2–4 Transformer layers
- small embedding dimension
- 2–4 attention heads
- dropout
- AdamW
- early stopping

These are starting points, not final values.

Use validation to tune them.

---

# 14. PHASE 11 — MIXED FEATURE OUTPUT

If state contains:

- continuous features
- binary features
- categorical distributions

do not force everything into a single naive MSE loss.

Consider separate heads:

```text
continuous head → regression loss
binary head → BCE
categorical head → cross entropy
```

Then combine losses.

Document the loss function.

---

# 15. PHASE 12 — ONE-STEP EVALUATION

Before K-step rollout, prove:

`S_t → S_hat_(t+1)`

Evaluate:

- feature-level prediction error
- state similarity
- attack-stage accuracy
- calibration
- temporal consistency

Save results.

If one-step prediction is poor, do NOT proceed to flashy K-step forecasting.

Fix the representation/model first.

---

# 16. PHASE 13 — K-STEP ROLLOUT

Implement:

```text
state = S_t

for k in range(K):
    predicted_state = world_model(state/history)
    state = predicted_state
```

Test:

K =

- 1
- 2
- 3
- 5

Do not assume K=5 is always best.

Measure error accumulation.

Create:

`src/prevail/rollout/`

and:

`docs/experiments/k-step-rollout.md`

---

# 17. PHASE 14 — FUTURE ATTACK PROBABILITY

From predicted future states:

```text
future states
      ↓
behavioural indicators
      ↓
attack-stage model
      ↓
P(stage at t+k)
```

Output:

```text
T+1 Recon             0.82
T+2 Discovery         0.74
T+3 Initial Access    0.63
T+4 Lateral Movement  0.51
T+5 C2                0.32
```

These probabilities must be calibrated/evaluated.

Do not display arbitrary confidence numbers.

---

# 18. PHASE 15 — MITRE ATT&CK MAPPING

Use MITRE ATT&CK as a structured interpretation layer.

Maintain a versioned mapping.

Example:

```text
predicted behaviour
       ↓
evidence
       ↓
candidate ATT&CK technique
       ↓
mapping confidence
```

Do not allow an LLM to autonomously invent ATT&CK mappings.

If an LLM is used at all, it must be outside the security-critical decision path and its output must be constrained/validated.

---

# 19. PHASE 16 — EXPLAINABILITY

Implement at least:

### Feature attribution

SHAP or another suitable attribution method.

### Temporal evidence

Show which historical windows contributed to the forecast.

Example:

```text
Prediction: Initial Access

Important evidence:

1. Destination-port sequence
2. SYN/ACK anomaly
3. connection burst
4. IAT shift
5. retransmission increase

Important windows:

T-3
T-2
T-1
T
```

Do not equate feature attribution with causality.

Use careful language:

“contributed to the model prediction.”

---

# 20. PHASE 17 — DEFENSIVE WHAT-IF SIMULATOR

This is PREVAIL's proposed innovation.

Do not implement until mandatory forecasting works.

Architecture:

```text
Current state
     ↓
Baseline forecast
     ↓
Intervention selector
     ↓
Modified simulated state
     ↓
World Model
     ↓
Counterfactual forecast
```

Example:

```text
Baseline:
Lateral Movement = 0.64
C2 = 0.48

Simulate:
Isolate Host A

New forecast:
Lateral Movement = 0.19
C2 = 0.07
```

Possible interventions:

- isolate host
- block source
- block destination port
- remove communication edge
- segment asset
- disable suspicious connection

Every intervention must have an explicit transformation function.

Create:

`docs/architecture/intervention-model.md`

For each intervention:

- precondition
- state modification
- assumptions
- limitations
- affected features
- expected side effects

Do not claim real-world causal effectiveness.

---

# 21. PHASE 18 — EXPERIMENT DESIGN

Create a proper experiment matrix.

At minimum:

### Experiment A
Logistic Regression baseline.

### Experiment B
Simple temporal baseline.

### Experiment C
Temporal Transformer one-step.

### Experiment D
Temporal Transformer K-step.

### Experiment E
Ablation: flow features only.

### Experiment F
Ablation: packet features only.

### Experiment G
Flow + packet features.

### Experiment H
Different window sizes.

### Experiment I
Different sequence lengths.

### Experiment J
Cross-scenario generalization.

### Experiment K
Intervention simulation.

Record:

- configuration
- dataset version
- seed
- code commit
- metrics
- artifacts

---

# 22. PHASE 19 — ABLATION STUDIES

This is important for proving that the architecture is not just hype.

Compare:

```text
Flow only
vs
Packet only
vs
Flow + Packet
```

Then:

```text
No temporal history
vs
Temporal history
```

Then:

```text
1-step
vs
K-step
```

Then:

```text
No intervention simulator
vs
intervention simulator
```

Use evidence to justify architecture decisions.

---

# 23. PHASE 20 — GENERALIZATION

Do not report only one random split.

Where feasible:

### Within-dataset temporal split

Train on earlier scenarios, test on later scenarios.

### Cross-attack split

Hold out selected attack scenarios.

### Cross-dataset validation

If resources allow:

Train on dataset A.

Test on dataset B.

If performance drops significantly, report it honestly.

Do not hide poor generalization.

---

# 24. PHASE 21 — OFFLINE OPERATION

The PS requires offline / air-gapped capability.

The final application must work without:

- cloud AI APIs
- external LLM APIs
- internet calls
- remote model inference

Package:

- trained model
- preprocessing pipeline
- mappings
- frontend
- backend
- dependencies

Use Docker for reproducibility.

Add an offline test:

```text
network disabled
      ↓
start application
      ↓
load sample telemetry
      ↓
forecast
      ↓
dashboard works
```

---

# 25. PHASE 22 — API

FastAPI endpoints:

```text
POST /api/v1/datasets/upload
POST /api/v1/analyze
POST /api/v1/forecast
POST /api/v1/rollout
POST /api/v1/intervention/simulate
GET  /api/v1/models
GET  /api/v1/experiments/{id}
GET  /api/v1/health
```

Do not expose arbitrary filesystem access.

Validate uploads.

Do not execute uploaded files.

PCAP parsing must be isolated and treated as untrusted input.

---

# 26. PHASE 23 — FRONTEND

Recommended:

Next.js + TypeScript.

Screens:

## Dashboard

Current network state.

## Forecast timeline

```text
T+1 → T+2 → T+3 → T+4 → T+5
```

## Attack trajectory

Graph of predicted stages.

## Explainability

Feature and temporal evidence.

## MITRE mapping

Technique/tactic information.

## What-if simulator

Select intervention → rerun forecast.

## Evaluation

Baseline vs World Model.

## Dataset / run management

Show reproducibility metadata.

---

# 27. PHASE 24 — VISUAL DEMO

The 2-minute demo should tell one story.

Example:

1. Load historical telemetry.
2. Show current network state.
3. PREVAIL detects a trajectory.
4. Show:
   `Recon → Discovery → Initial Access → Lateral Movement`
5. Click “Why?”
6. Show evidence.
7. Run K-step forecast.
8. Select “Isolate Host A”.
9. Run what-if simulation.
10. Show changed predicted trajectory.
11. Compare with Logistic Regression.
12. Show metrics.

Do not spend the demo explaining code.

---

# 28. PHASE 25 — SECURITY OF THE PRODUCT ITSELF

Treat PREVAIL as a security application.

Check:

- upload validation
- path traversal
- unsafe file parsing
- command injection
- API authentication if deployed
- CORS
- secrets
- dependency vulnerabilities
- model file integrity
- pickle/joblib security
- SSRF
- arbitrary code execution risks
- frontend XSS
- oversized PCAP denial-of-service
- resource exhaustion

Never load untrusted Python pickle files blindly.

Prefer safer model serialization where practical.

---

# 29. PHASE 26 — TESTING

Unit tests:

- feature calculations
- windowing
- state construction
- label mapping
- intervention transformations
- rollout
- probability calculations

Integration tests:

```text
dataset → preprocessing → state → model → rollout
```

Regression tests:

- fixed dataset
- fixed seed
- expected metrics within tolerance

Property tests:

- window timestamps remain ordered
- no future feature leakage
- intervention transformations preserve schema
- K-step rollout produces exactly K states
- probabilities stay in [0,1]

---

# 30. PHASE 27 — MLOPS / REPRODUCIBILITY

Every experiment must record:

```text
git commit
dataset version
feature version
model version
config
seed
hardware
metrics
timestamp
```

Use an experiment manifest.

Do not make results that cannot be reproduced.

---

# 31. PHASE 28 — DOCUMENTATION

Create:

```text
README.md
docs/research/prior-art.md
docs/research/differentiation.md
docs/requirements/SRS.md
docs/architecture/architecture.md
docs/architecture/data-contract.md
docs/architecture/threat-model.md
docs/architecture/intervention-model.md
docs/experiments/baseline.md
docs/experiments/world-model.md
docs/experiments/k-step.md
docs/experiments/ablation.md
docs/experiments/generalization.md
docs/demo/demo-script.md
docs/limitations.md
```

README must explain:

- problem
- why static IDS is insufficient
- World Model concept
- architecture
- datasets
- training
- evaluation
- offline operation
- demo
- limitations

---

# 32. PREVIOUS GITHUB PROJECTS — REFERENCE REQUIREMENT

The team has already identified public SIH26153 implementations/projects.

Claude MUST research and inspect those projects before finalizing architecture.

Use them as references for:

- feature engineering
- data pipeline
- model ideas
- temporal modelling
- dashboard ideas
- evaluation
- SIH presentation strategy

But:

## DO NOT COPY

Do not:

- copy source code
- copy README text
- copy diagrams
- copy UI
- copy project branding
- copy exact architecture and present it as original

Instead create a comparison table:

| Existing project | Useful feature | Keep? | Modify? | Why? |
|---|---|---|---|---|

If an existing project has a strong feature, we are allowed to **learn from it and independently reimplement an improved version**.

Explicitly record the source/reference.

Also inspect any new public SIH26153 projects discovered during research.

---

# 33. RESEARCH LOG

Maintain:

`docs/research/research-log.md`

Every important research decision must record:

```text
Date
Question
Sources checked
Finding
Decision
Reason
Impact
```

Example:

```text
Question:
Should we use a graph state?

Finding:
PS permits feature vector or graph representation.

Decision:
Start with feature vector.

Reason:
Lower implementation complexity and easier explainability.
Graph representation may be added after baseline if evidence shows benefit.
```

---

# 34. DECISION LOG

Maintain:

`DECISIONS.md`

Never silently change architecture.

Every major change:

```text
Decision
Context
Alternatives
Evidence
Chosen option
Reason
Trade-offs
```

---

# 35. IMPORTANT MODELING WARNINGS

Do NOT:

- call a static classifier a World Model
- randomly split temporally adjacent windows
- use future information in current-state features
- use ground-truth attack labels as input features
- report only accuracy
- fabricate confidence
- claim causal intervention effects
- claim novelty without prior-art evidence
- use an LLM as the core attack prediction engine
- hide poor cross-dataset performance
- compare models using different preprocessing
- tune on the test set
- select the best result from many experiments without reporting the selection process

---

# 36. ACCEPTANCE CRITERIA

The project is not considered complete until all are true:

## Research

- [ ] SIH PS requirements extracted
- [ ] prior-art research complete
- [ ] previous SIH projects reviewed
- [ ] differentiation documented

## Data

- [ ] dataset ingestion works
- [ ] feature pipeline reproducible
- [ ] temporal windows validated
- [ ] leakage checks pass
- [ ] attack-stage mappings documented

## ML

- [ ] Logistic Regression baseline
- [ ] World Model V1
- [ ] one-step prediction
- [ ] K-step rollout
- [ ] future attack probability
- [ ] ATT&CK mapping
- [ ] explainability

## Innovation

- [ ] what-if intervention simulator
- [ ] baseline vs intervention comparison
- [ ] limitations documented

## Evaluation

- [ ] Precision
- [ ] Recall
- [ ] F1
- [ ] False Positive Rate
- [ ] temporal evaluation
- [ ] ablation study
- [ ] generalization analysis

## Product

- [ ] FastAPI
- [ ] frontend
- [ ] offline operation
- [ ] Docker
- [ ] security testing
- [ ] automated tests

## SIH

- [ ] architecture diagram
- [ ] results charts
- [ ] demo dataset
- [ ] 2-minute demo flow
- [ ] presentation material
- [ ] technical report

---

# 37. EXECUTION ORDER FOR CLAUDE

Do NOT implement the entire project in one shot.

Execute in controlled milestones.

## Milestone 1 — Research

Produce:

- source-requirements.md
- prior-art.md
- differentiation.md
- open-questions.md

STOP and review.

## Milestone 2 — Data Contract

Produce:

- SRS
- data-contract
- state schema
- feature registry
- attack mapping draft

STOP and review.

## Milestone 3 — Data Pipeline

Implement:

- ingestion
- preprocessing
- state builder
- sequence builder
- leakage checks

Run tests.

STOP and review.

## Milestone 4 — Baseline

Implement Logistic Regression.

Produce baseline metrics.

STOP and review.

## Milestone 5 — World Model V1

Implement the smallest valid temporal Transformer.

Prove one-step prediction.

STOP and review.

## Milestone 6 — K-step Rollout

Implement and evaluate K-step prediction.

STOP and review.

## Milestone 7 — Attack Stage + ATT&CK

Implement interpretation layer.

STOP and review.

## Milestone 8 — Explainability

Implement feature + temporal evidence.

STOP and review.

## Milestone 9 — Intervention Simulator

Implement model-based what-if simulation.

STOP and review.

## Milestone 10 — Backend

Implement FastAPI.

STOP and review.

## Milestone 11 — Frontend

Build dashboard.

STOP and review.

## Milestone 12 — Evaluation + Hardening

Run full experiment matrix.

STOP and review.

## Milestone 13 — SIH Demo

Create polished demo and documentation.

---

# 38. HOW YOU MUST WORK

Act as a skeptical senior ML/security engineer.

When you find a weak assumption:

1. identify it
2. explain why it is weak
3. propose alternatives
4. test the alternative
5. document the decision

Do not blindly follow previous project architecture.

Do not blindly agree with this prompt.

If research proves a proposed design is wrong, change it and document why.

If the PS cannot support a claimed feature, say so.

If an existing GitHub project already implements a feature better, study it and determine whether we can improve or adapt the idea legitimately.

If you cannot verify something, say:

**“Not verified.”**

Do not fabricate citations, benchmarks, vulnerabilities, or novelty.

---

# 39. FIRST ACTION — DO THIS NOW

Before writing application code:

### Step 1
Inspect `/mnt/data/bugbounty guide.pdf`.

### Step 2
Research the official SIH26153 problem statement.

### Step 3
Find and inspect existing public SIH26153 implementations.

### Step 4
Create:

```text
docs/research/source-requirements.md
docs/research/prior-art.md
docs/research/differentiation.md
docs/research/open-questions.md
```

### Step 5
Create:

```text
docs/requirements/SRS.md
docs/architecture/data-contract.md
docs/architecture/architecture.md
```

### Step 6
Only after those are internally consistent, begin implementation.

Do NOT start by creating the dashboard.

The first technical implementation should be:

**dataset → temporal windows → NetworkState → sequence → leakage validation.**

---

# FINAL PRODUCT VISION

PREVAIL should ultimately answer four questions:

### 1. What is happening now?

Current network state.

### 2. What is likely to happen next?

K-step attack trajectory.

### 3. Why does the model think that?

Feature + temporal evidence.

### 4. What happens if the defender takes an action?

Model-based what-if forecast.

The final product should therefore be:

**not just an IDS,**

**not just an attack classifier,**

**not just a dashboard,**

but an **offline temporal network World Model that forecasts attack trajectories and provides evidence-backed future-state analysis, with a clearly labelled defensive what-if simulation extension.**

Build scientifically, document everything, and validate every claim.
