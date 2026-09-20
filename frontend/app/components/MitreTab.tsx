"use client";
import { useEffect, useState } from "react";
import { api, AttackMappingEntry } from "../../lib/api";

export default function MitreTab() {
  const [mappings, setMappings] = useState<Record<string, AttackMappingEntry> | null>(null);
  const [version, setVersion] = useState<string>("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    api
      .attackMapping()
      .then((r) => {
        setMappings(r.mappings);
        setVersion(r.attck_version_referenced);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="error-box">{error}</div>;
  if (!mappings) return <div className="muted">Loading ATT&amp;CK mapping...</div>;

  return (
    <div className="panel">
      <h2>MITRE ATT&amp;CK Mapping (reference)</h2>
      <p className="muted">{version}</p>
      {Object.entries(mappings)
        .filter(([, v]) => v.tactic)
        .map(([stage, v]) => (
          <div key={stage} className="panel" style={{ background: "#0f1620" }}>
            <div className="row" style={{ marginBottom: 6 }}>
              <strong style={{ textTransform: "capitalize" }}>{stage.replace("_", " ")}</strong>
              <span className={`badge confidence-${v.confidence}`}>{v.confidence} confidence</span>
            </div>
            <div className="muted">
              Tactic: <strong>{v.tactic!.name}</strong> ({v.tactic!.id}) &nbsp;|&nbsp; Technique:{" "}
              <strong>{v.technique?.name}</strong> ({v.technique?.id})
              {v.technique?.sub && <> — {v.technique.sub}</>}
            </div>
            <p style={{ fontSize: 12, whiteSpace: "pre-wrap" }}>{v.rationale}</p>
            <p className="muted" style={{ fontSize: 11 }}>Review status: {v.review_status}</p>
          </div>
        ))}
      <p className="disclaimer">
        Every mapping is hand-authored with an explicit confidence and rationale (configs/features/attack_stage_mapping.yaml)
        — never generated at runtime by an LLM.
      </p>
    </div>
  );
}
