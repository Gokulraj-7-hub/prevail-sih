# Experiment J — Generalization

**Data source: SYNTHETIC VALIDATION DATA (see DECISIONS.md D-003) — not a real-world benchmark result.**

## What IS covered, structurally, by every experiment in this repo

Every single result reported anywhere in `docs/experiments/` — baseline, World Model, K-step rollout, attack-stage, explainability, intervention, ablation — uses the **same scenario-level train/test split** (`sequences/split.py::scenario_train_test_split`, 30 train / 10 test scenarios, stratified by has_attack, zero overlap enforced and checked by `evaluation/data_quality.py`). No result anywhere in this repo comes from a random shuffle of adjacent temporal windows. This is itself a form of generalization test — every reported number already reflects performance on entirely unseen capture sessions, not memorized windows from sessions the model trained on (master prompt §2.4, §35).

## What is NOT yet run (tracked honestly, not hidden)

- **Dedicated cross-attack-type holdout**: e.g., training with zero `command_and_control` scenarios and testing generalization to that stage specifically. Not run this pass — would require re-splitting scenarios by which attack stages they contain rather than by has_attack alone, and the synthetic dataset's 25 attack scenarios all contain the full recon→initial_access→lateral_movement→C2 timeline (see `ingestion/synthetic.py`), so there is currently no scenario that contains, say, lateral_movement without C2 to hold out cleanly. This would need a generator change first.
- **Cross-dataset validation** (train on dataset A, test on dataset B): not possible yet — only one dataset (the synthetic generator) exists in this repo. This is the single most important generalization test still missing, and it's blocked on the same open item as everywhere else in this repo: real-dataset integration (`docs/research/open-questions.md` OQ-2).

## Reading

Per master prompt §20: "if performance drops significantly [across a real generalization test], report it honestly, do not hide poor generalization." No such test has been run yet, so there is nothing to report either way — and this doc says so rather than implying generalization has been validated when it has not.
