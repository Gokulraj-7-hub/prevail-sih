const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export interface AnalyzeResponse {
  scenario_id: string;
  n_windows: number;
  latest_window_id: number;
  latest_attack_stage: string;
  latest_attack_label: number;
  window_size_s: number;
}

export interface ForecastStep {
  step: number;
  predicted_stage: string;
  stage_probability: number;
  p_attack: number;
  attck_tactic: { id: string; name: string } | null;
  attck_technique: { id: string; name: string; sub?: string } | null;
  attck_mapping_confidence: string;
}

export interface ForecastResponse {
  scenario_id: string;
  history_end_window_id: number;
  table: ForecastStep[];
}

export interface InterventionStepComparison {
  step: number;
  baseline_p_attack: number;
  counterfactual_p_attack: number;
  delta: number;
}

export interface InterventionResponse {
  scenario_id: string;
  intervention_name: string;
  intervention_description: string;
  ood_score: number;
  ood_flagged: boolean;
  comparison: InterventionStepComparison[];
  disclaimer: string;
}

export interface ModelInfo {
  name: string;
  manifest: Record<string, unknown>;
}

export interface UploadResponse {
  dataset_id: string;
  scenario_ids: string[];
  n_states: number;
}

export interface ExplainResponse {
  scenario_id: string;
  predicted_stage: string;
  feature_evidence: { feature: string; shap_value: number; direction: string }[];
  temporal_evidence: { label: string; importance_normalized: number }[];
  disclaimer: string;
}

export interface AttackMappingEntry {
  tactic: { id: string; name: string } | null;
  technique: { id: string; name: string; sub?: string } | null;
  confidence: string;
  rationale: string;
  review_status: string;
}

export const api = {
  health: () => request<{ status: string; models_loaded: boolean }>("/health"),

  scenarios: (dataset_id: string) =>
    request<{ dataset_id: string; scenario_ids: string[] }>(`/datasets/${dataset_id}/scenarios`),

  analyze: (dataset_id: string, scenario_id: string) =>
    request<AnalyzeResponse>("/analyze", {
      method: "POST",
      body: JSON.stringify({ dataset_id, scenario_id }),
    }),

  forecast: (dataset_id: string, scenario_id: string, end_window_id: number, K: number, seq_len = 10) =>
    request<ForecastResponse>("/forecast", {
      method: "POST",
      body: JSON.stringify({ dataset_id, scenario_id, end_window_id, K, seq_len }),
    }),

  simulateIntervention: (
    dataset_id: string,
    scenario_id: string,
    end_window_id: number,
    K: number,
    intervention_type: string,
    params: Record<string, unknown>
  ) =>
    request<InterventionResponse>("/intervention/simulate", {
      method: "POST",
      body: JSON.stringify({ dataset_id, scenario_id, end_window_id, K, intervention_type, params }),
    }),

  explain: (dataset_id: string, scenario_id: string, end_window_id: number, seq_len = 10) =>
    request<ExplainResponse>("/explain", {
      method: "POST",
      body: JSON.stringify({ dataset_id, scenario_id, end_window_id, seq_len }),
    }),

  attackMapping: () =>
    request<{ attck_version_referenced: string; mappings: Record<string, AttackMappingEntry> }>("/attack-mapping"),

  models: () => request<ModelInfo[]>("/models"),

  experiment: (id: string) => request<Record<string, unknown>>(`/experiments/${id}`),

  upload: async (file: File): Promise<UploadResponse> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/datasets/upload`, { method: "POST", body: form });
    if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
    return res.json();
  },
};
