"use client";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export interface SelectionState {
  datasetId: string;
  scenarioId: string;
  endWindowId: number;
  K: number;
}

export default function Controls({
  selection,
  onChange,
}: {
  selection: SelectionState;
  onChange: (s: SelectionState) => void;
}) {
  const [scenarios, setScenarios] = useState<string[]>([]);
  const [uploadStatus, setUploadStatus] = useState<string>("");

  useEffect(() => {
    api
      .scenarios(selection.datasetId)
      .then((r) => setScenarios(r.scenario_ids))
      .catch(() => setScenarios([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selection.datasetId]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadStatus("Uploading...");
    try {
      const res = await api.upload(file);
      setUploadStatus(`Uploaded: ${res.dataset_id} (${res.scenario_ids.length} scenario(s), ${res.n_states} states)`);
      onChange({ ...selection, datasetId: res.dataset_id, scenarioId: res.scenario_ids[0] || "" });
    } catch (err) {
      setUploadStatus(`Upload failed: ${(err as Error).message}`);
    }
  }

  return (
    <div className="panel">
      <h3>Dataset / Run Selection</h3>
      <div className="row">
        <label className="muted">Dataset</label>
        <input
          className="mono"
          value={selection.datasetId}
          onChange={(e) => onChange({ ...selection, datasetId: e.target.value })}
          style={{ width: 160 }}
        />
        <label className="muted">Scenario</label>
        {scenarios.length > 0 ? (
          <select value={selection.scenarioId} onChange={(e) => onChange({ ...selection, scenarioId: e.target.value })}>
            {scenarios.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        ) : (
          <input
            className="mono"
            value={selection.scenarioId}
            onChange={(e) => onChange({ ...selection, scenarioId: e.target.value })}
            style={{ width: 160 }}
          />
        )}
        <label className="muted">History end window</label>
        <input
          type="number"
          value={selection.endWindowId}
          onChange={(e) => onChange({ ...selection, endWindowId: Number(e.target.value) })}
          style={{ width: 70 }}
        />
        <label className="muted">K (forecast steps)</label>
        <input
          type="number"
          min={1}
          max={10}
          value={selection.K}
          onChange={(e) => onChange({ ...selection, K: Number(e.target.value) })}
          style={{ width: 60 }}
        />
      </div>
      <div className="row">
        <label className="muted">Upload telemetry CSV (packet-event schema)</label>
        <input type="file" accept=".csv" onChange={handleUpload} />
        {uploadStatus && <span className="muted">{uploadStatus}</span>}
      </div>
    </div>
  );
}
