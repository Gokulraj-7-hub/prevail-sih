"use client";
import { useEffect, useState } from "react";
import { api, ModelInfo } from "../../lib/api";

function metricPath(manifest: Record<string, unknown>, ...path: string[]): unknown {
  let cur: unknown = manifest;
  for (const p of path) {
    if (cur && typeof cur === "object" && p in (cur as Record<string, unknown>)) {
      cur = (cur as Record<string, unknown>)[p];
    } else {
      return undefined;
    }
  }
  return cur;
}

function fmt(v: unknown): string {
  if (typeof v === "number") return v.toFixed(3);
  if (v === undefined || v === null) return "-";
  return String(v);
}

export default function EvaluationTab() {
  const [models, setModels] = useState<ModelInfo[] | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    api.models().then(setModels).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="error-box">{error}</div>;
  if (!models) return <div className="muted">Loading experiment manifests...</div>;

  const baseline = models.find((m) => m.name === "baseline");
  const worldModel = models.find((m) => m.name === "world_model");

  return (
    <div className="panel">
      <h2>Baseline vs. World Model (Experiment A vs. C)</h2>
      <p className="disclaimer" style={{ marginTop: 0 }}>
        SYNTHETIC VALIDATION DATA — not a real-world benchmark result. See docs/experiments/*.md.
      </p>

      {baseline && (
        <>
          <h3>Logistic Regression baseline (test split)</h3>
          <table>
            <tbody>
              <tr>
                <td>Precision</td>
                <td className="mono">{fmt(metricPath(baseline.manifest, "metrics", "test", "precision"))}</td>
              </tr>
              <tr>
                <td>Recall</td>
                <td className="mono">{fmt(metricPath(baseline.manifest, "metrics", "test", "recall"))}</td>
              </tr>
              <tr>
                <td>F1</td>
                <td className="mono">{fmt(metricPath(baseline.manifest, "metrics", "test", "f1"))}</td>
              </tr>
              <tr>
                <td>False Positive Rate</td>
                <td className="mono">{fmt(metricPath(baseline.manifest, "metrics", "test", "false_positive_rate"))}</td>
              </tr>
              <tr>
                <td>ROC-AUC</td>
                <td className="mono">{fmt(metricPath(baseline.manifest, "metrics", "test", "roc_auc"))}</td>
              </tr>
            </tbody>
          </table>
        </>
      )}

      {worldModel && (
        <>
          <h3 style={{ marginTop: 20 }}>World Model V1 — one-step (test scenarios)</h3>
          <table>
            <tbody>
              <tr>
                <td>Normalized MSE</td>
                <td className="mono">
                  {fmt(metricPath(worldModel.manifest, "metrics", "feature_level_error", "overall_mse_normalized"))}
                </td>
              </tr>
              <tr>
                <td>Mean cosine similarity</td>
                <td className="mono">
                  {fmt(metricPath(worldModel.manifest, "metrics", "state_similarity", "mean_cosine_similarity"))}
                </td>
              </tr>
              <tr>
                <td>Auxiliary stage accuracy</td>
                <td className="mono">
                  {fmt(metricPath(worldModel.manifest, "metrics", "attack_stage_accuracy", "accuracy"))}
                </td>
              </tr>
            </tbody>
          </table>
        </>
      )}

      <h3 style={{ marginTop: 20 }}>All experiment manifests</h3>
      <table>
        <thead>
          <tr>
            <th>Experiment</th>
            <th>Git commit</th>
            <th>Seed</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {models.map((m) => (
            <tr key={m.name}>
              <td className="mono">{m.name}</td>
              <td className="mono">{String(metricPath(m.manifest, "git_commit")).slice(0, 10)}</td>
              <td className="mono">{fmt(metricPath(m.manifest, "seed"))}</td>
              <td className="mono">{fmt(metricPath(m.manifest, "timestamp_utc"))}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
