"use client";
import { useState } from "react";
import Controls, { SelectionState } from "./components/Controls";
import OverviewTab from "./components/OverviewTab";
import ForecastTab from "./components/ForecastTab";
import TrajectoryTab from "./components/TrajectoryTab";
import ExplainabilityTab from "./components/ExplainabilityTab";
import MitreTab from "./components/MitreTab";
import WhatIfTab from "./components/WhatIfTab";
import EvaluationTab from "./components/EvaluationTab";

const TABS = [
  { key: "overview", label: "Dashboard" },
  { key: "forecast", label: "Forecast Timeline" },
  { key: "trajectory", label: "Attack Trajectory" },
  { key: "explain", label: "Explainability" },
  { key: "mitre", label: "MITRE Mapping" },
  { key: "whatif", label: "What-If Simulator" },
  { key: "eval", label: "Evaluation" },
];

export default function Home() {
  const [tab, setTab] = useState("overview");
  const [selection, setSelection] = useState<SelectionState>({
    datasetId: "demo",
    scenarioId: "scn_009_attack",
    endWindowId: 21,
    K: 5,
  });

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">PREVAIL</div>
        <div className="brand-sub">SIH26153 — Attack Trajectory Forecasting</div>
        <div className="data-banner">All figures shown are from a synthetic validation dataset, not real-world telemetry.</div>
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`nav-item ${tab === t.key ? "active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </aside>
      <main className="main">
        <Controls selection={selection} onChange={setSelection} />
        {tab === "overview" && <OverviewTab selection={selection} />}
        {tab === "forecast" && <ForecastTab selection={selection} />}
        {tab === "trajectory" && <TrajectoryTab selection={selection} />}
        {tab === "explain" && <ExplainabilityTab selection={selection} />}
        {tab === "mitre" && <MitreTab />}
        {tab === "whatif" && <WhatIfTab selection={selection} />}
        {tab === "eval" && <EvaluationTab />}
      </main>
    </div>
  );
}
