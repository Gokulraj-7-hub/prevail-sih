"use client";
import { useState } from "react";
import { api, InterventionResponse } from "../../lib/api";
import { SelectionState } from "./Controls";

const INTERVENTION_TYPES: { value: string; label: string; params: { key: string; label: string; placeholder: string }[] }[] = [
  { value: "block_destination_port", label: "Block destination port", params: [{ key: "port", label: "Port", placeholder: "8080" }] },
  { value: "isolate_host", label: "Isolate host", params: [{ key: "host_ip", label: "Host IP", placeholder: "10.0.x.x" }] },
  { value: "block_source", label: "Block source", params: [{ key: "src_ip", label: "Source IP", placeholder: "x.x.x.x" }] },
  {
    value: "remove_communication_edge",
    label: "Remove communication edge",
    params: [
      { key: "ip_a", label: "Host A", placeholder: "10.0.x.x" },
      { key: "ip_b", label: "Host B", placeholder: "10.0.x.x" },
    ],
  },
  {
    value: "disable_suspicious_connection",
    label: "Disable suspicious connection",
    params: [
      { key: "src_ip", label: "Source IP", placeholder: "x.x.x.x" },
      { key: "dst_ip", label: "Destination IP", placeholder: "10.0.x.x" },
      { key: "dst_port", label: "Destination port", placeholder: "445" },
    ],
  },
];

export default function WhatIfTab({ selection }: { selection: SelectionState }) {
  const [interventionType, setInterventionType] = useState(INTERVENTION_TYPES[0].value);
  const [params, setParams] = useState<Record<string, string>>({ port: "8080" });
  const [result, setResult] = useState<InterventionResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const spec = INTERVENTION_TYPES.find((t) => t.value === interventionType)!;

  async function run() {
    setLoading(true);
    setError("");
    try {
      const numericParams: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(params)) {
        numericParams[k] = /^\d+$/.test(v) ? Number(v) : v;
      }
      const res = await api.simulateIntervention(
        selection.datasetId,
        selection.scenarioId,
        selection.endWindowId,
        selection.K,
        interventionType,
        numericParams
      );
      setResult(res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <h2>Defensive What-If Simulator</h2>
      <p className="muted">
        Proposed extension beyond the mandatory PS requirement. See docs/architecture/intervention-model.md.
      </p>

      <div className="row">
        <select
          value={interventionType}
          onChange={(e) => {
            setInterventionType(e.target.value);
            setParams({});
          }}
        >
          {INTERVENTION_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
        {spec.params.map((p) => (
          <input
            key={p.key}
            placeholder={`${p.label} (${p.placeholder})`}
            value={params[p.key] || ""}
            onChange={(e) => setParams({ ...params, [p.key]: e.target.value })}
            style={{ width: 160 }}
          />
        ))}
        <button className="action" onClick={run} disabled={loading}>
          {loading ? "Simulating..." : "Run simulation"}
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      {result && (
        <>
          <div className="row">
            <strong>{result.intervention_name}</strong>
            <span className={`badge ${result.ood_flagged ? "confidence-low" : "confidence-medium"}`}>
              OOD score {result.ood_score.toFixed(2)} {result.ood_flagged ? "(flagged: unusual)" : "(normal range)"}
            </span>
          </div>
          <p className="muted">{result.intervention_description}</p>
          <table>
            <thead>
              <tr>
                <th>Step</th>
                <th>Baseline P(attack)</th>
                <th>Counterfactual P(attack)</th>
                <th>Delta</th>
              </tr>
            </thead>
            <tbody>
              {result.comparison.map((c) => (
                <tr key={c.step}>
                  <td className="mono">T+{c.step}</td>
                  <td className="mono">{c.baseline_p_attack.toFixed(3)}</td>
                  <td className="mono">{c.counterfactual_p_attack.toFixed(3)}</td>
                  <td className="mono" style={{ color: c.delta < 0 ? "var(--ok)" : "var(--danger)" }}>
                    {c.delta >= 0 ? "+" : ""}
                    {c.delta.toFixed(3)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="disclaimer">{result.disclaimer}</p>
        </>
      )}
    </div>
  );
}
