"use client";
import { Fragment, useEffect, useState } from "react";
import { api, ForecastResponse } from "../../lib/api";
import { SelectionState } from "./Controls";

export default function TrajectoryTab({ selection }: { selection: SelectionState }) {
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
  if (!data) return <div className="muted">Loading trajectory...</div>;

  return (
    <div className="panel">
      <h2>Predicted Attack Trajectory</h2>
      <div className="trajectory-chain">
        <div className="trajectory-node">
          <div className="muted">Current</div>
          <strong>(observed)</strong>
        </div>
        {data.table.map((row, i) => (
          <Fragment key={row.step}>
            <span className="trajectory-arrow">→</span>
            <div className="trajectory-node">
              <div className="muted">T+{row.step}</div>
              <strong>{row.predicted_stage.replace("_", " ")}</strong>
              <div className="muted mono">{(row.p_attack * 100).toFixed(0)}%</div>
            </div>
          </Fragment>
        ))}
      </div>
      <p className="disclaimer">
        This chain is the model&apos;s forecast, not an observed sequence of events. Read as &quot;the model
        currently forecasts this progression,&quot; not as a certainty.
      </p>
    </div>
  );
}
