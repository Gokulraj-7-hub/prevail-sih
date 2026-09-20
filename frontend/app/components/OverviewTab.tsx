"use client";
import { useEffect, useState } from "react";
import { api, AnalyzeResponse } from "../../lib/api";
import { SelectionState } from "./Controls";

export default function OverviewTab({ selection }: { selection: SelectionState }) {
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    setError("");
    api
      .analyze(selection.datasetId, selection.scenarioId)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [selection.datasetId, selection.scenarioId]);

  if (error) return <div className="error-box">{error}</div>;
  if (!data) return <div className="muted">Loading current network state...</div>;

  const isAttack = data.latest_attack_label === 1;

  return (
    <div className="panel">
      <h2>Current Network State</h2>
      <table>
        <tbody>
          <tr>
            <td>Scenario</td>
            <td className="mono">{data.scenario_id}</td>
          </tr>
          <tr>
            <td>Total windows captured</td>
            <td>{data.n_windows}</td>
          </tr>
          <tr>
            <td>Latest window id</td>
            <td>{data.latest_window_id}</td>
          </tr>
          <tr>
            <td>Window size</td>
            <td>{data.window_size_s}s</td>
          </tr>
          <tr>
            <td>Latest observed stage</td>
            <td>
              <span className={`badge ${isAttack ? "attack" : "benign"}`}>{data.latest_attack_stage}</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p className="disclaimer">
        This reflects the ground-truth-labeled state of the LAST captured window in this scenario (for the demo
        dataset). The Forecast tab predicts windows beyond the &quot;History end window&quot; selected in the
        controls above, which may be earlier than this latest window.
      </p>
    </div>
  );
}
