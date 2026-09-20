"use client";
import { useEffect, useState } from "react";
import { api, ExplainResponse } from "../../lib/api";
import { SelectionState } from "./Controls";

export default function ExplainabilityTab({ selection }: { selection: SelectionState }) {
  const [data, setData] = useState<ExplainResponse | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    setError("");
    api
      .explain(selection.datasetId, selection.scenarioId, selection.endWindowId)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [selection.datasetId, selection.scenarioId, selection.endWindowId]);

  if (error) return <div className="error-box">{error}</div>;
  if (!data) return <div className="muted">Loading explanation...</div>;

  const maxTemporal = Math.max(...data.temporal_evidence.map((t) => t.importance_normalized), 1e-6);

  return (
    <div className="panel">
      <h2>
        Why? — Prediction: <span className="badge attack">{data.predicted_stage}</span>
      </h2>

      <h3>Feature evidence (SHAP, top contributors to T+1)</h3>
      <table>
        <tbody>
          {data.feature_evidence.map((f) => (
            <tr key={f.feature}>
              <td className="mono">{f.feature}</td>
              <td>{f.direction} confidence</td>
              <td className="mono">{f.shap_value.toFixed(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3 style={{ marginTop: 20 }}>Temporal evidence (which historical windows mattered most)</h3>
      <table>
        <tbody>
          {data.temporal_evidence.slice(0, 6).map((t) => (
            <tr key={t.label}>
              <td className="mono" style={{ width: 50 }}>
                {t.label}
              </td>
              <td>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(t.importance_normalized / maxTemporal) * 100}%` }} />
                </div>
              </td>
              <td className="mono" style={{ width: 60 }}>
                {t.importance_normalized.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="disclaimer">{data.disclaimer}</p>
    </div>
  );
}
