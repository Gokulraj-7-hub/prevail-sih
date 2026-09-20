"""Data quality report (master prompt Phase 8/11). Writes artifacts/data_quality_report.html.

Fails loudly (raises) on critical leakage rather than silently producing a report,
per master prompt: "Fail the pipeline if critical leakage is detected."
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from prevail.preprocessing.clean import QualityReport
from prevail.sequences.split import assert_no_scenario_overlap


def run_leakage_checks(train_ids: list[str], test_ids: list[str]) -> None:
    assert_no_scenario_overlap(train_ids, test_ids)


def build_data_quality_report(
    packets: pd.DataFrame,
    clean_report: QualityReport,
    states: pd.DataFrame,
    scenario_meta: pd.DataFrame,
    train_ids: list[str],
    test_ids: list[str],
    out_path: str | Path,
) -> None:
    run_leakage_checks(train_ids, test_ids)  # raises on failure -- pipeline halts

    label_dist = states["attack_stage"].value_counts()
    class_balance = states["attack_label"].value_counts(normalize=True)

    feature_cols = [c for c in states.columns if "__" in c]
    numeric = states[feature_cols].apply(pd.to_numeric, errors="coerce")
    outlier_pct = ((numeric - numeric.mean()).abs() > 4 * numeric.std(ddof=0)).mean().sort_values(ascending=False).head(15)

    train_stage_dist = states[states["scenario_id"].isin(train_ids)]["attack_stage"].value_counts(normalize=True)
    test_stage_dist = states[states["scenario_id"].isin(test_ids)]["attack_stage"].value_counts(normalize=True)

    html_parts = [
        "<html><head><title>PREVAIL Data Quality Report</title>",
        "<style>body{font-family:sans-serif;margin:2em} table{border-collapse:collapse} "
        "td,th{border:1px solid #ccc;padding:4px 10px;text-align:left}</style></head><body>",
        "<h1>PREVAIL Data Quality Report</h1>",
        "<p><b>Data source:</b> synthetic validation dataset (see DECISIONS.md D-003) "
        "-- these figures characterize pipeline behaviour, not real-world telemetry.</p>",
        "<h2>Preprocessing / cleaning</h2>",
        f"<pre>{clean_report.as_dict()}</pre>",
        "<h2>Scenario / leakage checks</h2>",
        f"<p>Train scenarios: {len(train_ids)} | Test scenarios: {len(test_ids)} | "
        f"Overlap: 0 (verified, pipeline halts otherwise)</p>",
        "<h2>Label distribution (attack_stage, all states)</h2>",
        label_dist.to_frame("count").to_html(),
        "<h2>Class balance (attack_label)</h2>",
        class_balance.to_frame("fraction").to_html(),
        "<h2>Attack-stage distribution: train vs test</h2>",
        pd.DataFrame({"train": train_stage_dist, "test": test_stage_dist}).fillna(0.0).to_html(),
        "<h2>Feature outlier rate (fraction of rows >4 std from mean, top 15 features)</h2>",
        outlier_pct.to_frame("outlier_fraction").to_html(),
        "<h2>Feature summary statistics</h2>",
        numeric.describe().T.to_html(),
        "</body></html>",
    ]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(html_parts))
