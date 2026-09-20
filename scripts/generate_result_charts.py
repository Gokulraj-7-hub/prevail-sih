#!/usr/bin/env python
"""SIH demo materials (Milestone 13): render the real numbers already in
artifacts/*.json / manifest.json as chart images. No new experiments run
here -- every chart is a visualization of a result already reported (and
labeled as synthetic-validation-data) in docs/experiments/*.md."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "charts"
OUT.mkdir(parents=True, exist_ok=True)

CAPTION = "Synthetic validation dataset — not a real-world benchmark result"
plt.rcParams.update({"figure.dpi": 140, "font.size": 10})


def _load(path):
    with open(path) as f:
        return json.load(f)


def chart_k_step_error():
    data = _load(ROOT / "artifacts" / "rollout" / "k_step_results.json")
    steps = [1, 2, 3, 5]
    mse = [data[f"K={k}"]["per_step"][-1]["normalized_mse"] for k in steps]
    f1 = [data[f"K={k}"]["per_step"][-1]["f1"] for k in steps]
    fpr = [data[f"K={k}"]["per_step"][-1]["false_positive_rate"] for k in steps]

    fig, ax1 = plt.subplots(figsize=(6, 4))
    ax1.plot(steps, mse, "o-", color="#c0392b", label="Normalized MSE (error accumulation)")
    ax1.set_xlabel("Rollout horizon K (steps)")
    ax1.set_ylabel("Normalized MSE", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#c0392b")
    ax1.set_xticks(steps)

    ax2 = ax1.twinx()
    ax2.plot(steps, f1, "s--", color="#2980b9", label="Stage F1")
    ax2.plot(steps, fpr, "^:", color="#27ae60", label="FPR")
    ax2.set_ylabel("F1 / FPR", color="#2980b9")

    fig.legend(loc="upper center", bbox_to_anchor=(0.5, 0.02), ncol=3, fontsize=8)
    plt.title("K-step rollout: error accumulates, FPR stays flat")
    plt.figtext(0.5, -0.08, CAPTION, ha="center", fontsize=8, style="italic", color="gray")
    plt.tight_layout()
    plt.savefig(OUT / "k_step_error_accumulation.png", bbox_inches="tight")
    plt.close()


def chart_ablation():
    data = _load(ROOT / "artifacts" / "ablation" / "feature_family_ablation.json")
    names = list(data.keys())
    f1 = [data[n]["test_metrics"]["f1"] for n in names]
    fpr = [data[n]["test_metrics"]["false_positive_rate"] for n in names]

    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(names))
    ax.bar([i - 0.2 for i in x], f1, width=0.4, label="F1", color="#2980b9")
    ax.bar([i + 0.2 for i in x], fpr, width=0.4, label="FPR", color="#c0392b")
    ax.set_xticks(list(x))
    ax.set_xticklabels([n.replace(" (baseline default)", "\n(default)") for n in names], rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("Score")
    ax.legend()
    plt.title("Feature-family ablation (Experiments E/F/G)")
    plt.figtext(0.5, -0.12, CAPTION, ha="center", fontsize=8, style="italic", color="gray")
    plt.tight_layout()
    plt.savefig(OUT / "feature_family_ablation.png", bbox_inches="tight")
    plt.close()


def chart_baseline_vs_worldmodel():
    baseline = _load(ROOT / "artifacts" / "baseline" / "manifest.json")
    wm = _load(ROOT / "artifacts" / "world_model" / "manifest.json")

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))

    bm = baseline["metrics"]["test"]
    labels = ["Precision", "Recall", "F1", "FPR", "ROC-AUC"]
    vals = [bm["precision"], bm["recall"], bm["f1"], bm["false_positive_rate"], bm["roc_auc"]]
    axes[0].bar(labels, vals, color="#8e44ad")
    axes[0].set_ylim(0, 1)
    axes[0].set_title("Experiment A: Logistic Regression\n(one-step-ahead, test scenarios)")
    axes[0].tick_params(axis="x", labelrotation=30)

    wm_labels = ["Norm. MSE\n(lower better)", "Cosine sim.", "Aux stage acc.", "Trend corr."]
    wm_vals = [
        wm["metrics"]["feature_level_error"]["overall_mse_normalized"],
        wm["metrics"]["state_similarity"]["mean_cosine_similarity"],
        wm["metrics"]["attack_stage_accuracy"]["accuracy"],
        wm["metrics"]["temporal_consistency"]["trend_correlation"],
    ]
    axes[1].bar(wm_labels, wm_vals, color="#16a085")
    axes[1].set_ylim(0, 1)
    axes[1].set_title("Experiment C: World Model V1\n(one-step, test scenarios)")
    axes[1].tick_params(axis="x", labelrotation=30)

    plt.figtext(0.5, -0.05, CAPTION, ha="center", fontsize=8, style="italic", color="gray")
    plt.tight_layout()
    plt.savefig(OUT / "baseline_vs_world_model.png", bbox_inches="tight")
    plt.close()


def chart_attack_stage_per_class():
    manifest = _load(ROOT / "artifacts" / "attack_stage" / "manifest.json")
    report = manifest["metrics"]["classification_report"]
    stages = ["benign", "recon", "initial_access", "lateral_movement", "command_and_control"]
    precision = [report[s]["precision"] for s in stages]
    recall = [report[s]["recall"] for s in stages]
    support = [int(report[s]["support"]) for s in stages]

    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(stages))
    ax.bar([i - 0.2 for i in x], precision, width=0.4, label="Precision", color="#2980b9")
    ax.bar([i + 0.2 for i in x], recall, width=0.4, label="Recall", color="#e67e22")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{s}\n(n={n})" for s, n in zip(stages, support)], fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.legend()
    plt.title("Attack-stage classifier: precision/recall by class\n(rare classes have low sample support -- read with caution)")
    plt.figtext(0.5, -0.1, CAPTION, ha="center", fontsize=8, style="italic", color="gray")
    plt.tight_layout()
    plt.savefig(OUT / "attack_stage_per_class.png", bbox_inches="tight")
    plt.close()


def chart_intervention():
    data = _load(ROOT / "artifacts" / "intervention" / "demo_comparison.json")
    steps = list(range(1, len(data["baseline_p_attack"]) + 1))

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(steps, data["baseline_p_attack"], "o-", label="Baseline (no intervention)", color="#7f8c8d", linewidth=2)
    colors = ["#c0392b", "#8e44ad"]
    for iv, color in zip(data["interventions"], colors):
        ax.plot(steps, iv["counterfactual_p_attack"], "s--", label=iv["name"], color=color)
    ax.set_xlabel("Forecast step (T+k)")
    ax.set_ylabel("P(attack)")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(steps)
    ax.legend(fontsize=8)
    plt.title("What-if simulator: both tested interventions INCREASED forecast P(attack)\n(honest result -- see docs/experiments/intervention.md)")
    plt.figtext(0.5, -0.1, CAPTION, ha="center", fontsize=8, style="italic", color="gray")
    plt.tight_layout()
    plt.savefig(OUT / "intervention_comparison.png", bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    chart_k_step_error()
    chart_ablation()
    chart_baseline_vs_worldmodel()
    chart_attack_stage_per_class()
    chart_intervention()
    print(f"Charts written to {OUT}")
    for p in sorted(OUT.glob("*.png")):
        print(f"  {p.name}")
