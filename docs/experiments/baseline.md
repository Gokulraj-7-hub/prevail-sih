# Experiment A — Logistic Regression Baseline

**Data source: SYNTHETIC VALIDATION DATA (see DECISIONS.md D-003) — not a real-world benchmark result.**

- Config: `C=1.0`, `class_weight=balanced`, seed 42, window 5s, seq_len 10.
- Task (D-006): one-step-ahead forecast — input is the current window's own 59-feature vector, target is whether the *next* window is an attack.
- Split: 30/10 scenario-level train/test split (stratified by has_attack), zero scenario overlap (enforced, see `evaluation/data_quality.py`).
- Artifacts: `artifacts/baseline/logistic_regression.joblib`, `manifest.json`, `coefficients_top20.txt`.

## Results

| Split | Precision | Recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| Train | 0.887 | 0.872 | 0.879 | 0.027 | 0.959 | 0.901 |
| Test  | 0.833 | 0.812 | 0.823 | 0.050 | 0.870 | 0.798 |

Test confusion matrix: TN=364, FP=19, FN=22, TP=95 (positive rate 23.4%).

## Reading

Train-to-test metric drop (F1 0.879 -> 0.823, ROC-AUC 0.959 -> 0.870) is consistent with ordinary generalization gap on a held-out *scenario* split (not memorized adjacent windows), and the test numbers are not implausibly perfect — no reason to suspect leakage. This is the baseline `evaluation/*` will compare the World Model against for FR-15.
