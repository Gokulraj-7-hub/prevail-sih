"use client";
import { useEffect, useState } from "react";
import { api, ForecastResponse } from "../../lib/api";
import { SelectionState } from "./Controls";

export default function ForecastTab({ selection }: { selection: SelectionState }) {
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    setError("");
    api
      .forecast(selection.datasetId, selection.scenarioId, selection.endWindowId, selection.K)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [selection.datasetId, selection.scenarioId, selection.endWindowId, selection.K]);

  if (error) return <div className="error-box">{error}</div>;
  if (!data) return <div className="muted">Loading forecast...</div>;

  return (
    <div className="panel">
      <h2>Forecast Timeline (K-step rollout)</h2>
      <table>
        <thead>
          <tr>
            <th>Step</th>
            <th>Predicted stage</th>
            <th>P(attack)</th>
            <th>ATT&CK tactic</th>
            <th>Mapping confidence</th>
          </tr>
        </thead>
        <tbody>
          {data.table.map((row) => (
            <tr key={row.step}>
              <td className="mono">T+{row.step}</td>
              <td>
                <span className={`badge ${row.predicted_stage === "benign" ? "benign" : "attack"}`}>
                  {row.predicted_stage}
                </span>
              </td>
              <td style={{ minWidth: 160 }}>
                <div className="row" style={{ margin: 0, gap: 8 }}>
                  <div className="bar-track" style={{ maxWidth: 100 }}>
                    <div
                      className={`bar-fill ${row.p_attack > 0.5 ? "danger" : ""}`}
                      style={{ width: `${Math.round(row.p_attack * 100)}%` }}
                    />
                  </div>
                  <span className="mono">{row.p_attack.toFixed(2)}</span>
                </div>
              </td>
              <td>{row.attck_tactic ? `${row.attck_tactic.name} (${row.attck_tactic.id})` : "-"}</td>
              <td>
                {row.attck_mapping_confidence !== "n/a" && (
                  <span className={`badge confidence-${row.attck_mapping_confidence}`}>
                    {row.attck_mapping_confidence}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="disclaimer">
        Per-step confidence decreases with K (see docs/experiments/k-step.md): error accumulates through the
        rollout, so a T+5 forecast should be trusted less than T+1. Reported normalized MSE rises from ~0.38 at
        T+1 to ~0.77 at T+5 on the synthetic validation set.
      </p>
    </div>
  );
}
