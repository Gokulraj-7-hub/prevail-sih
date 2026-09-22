"""PREVAIL FastAPI backend (Phase 22). Fully offline at inference time -- no
outbound network calls anywhere in this module (SRS.md offline NFR)."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from prevail.api.dataset_store import DatasetStore, IngestionError
from prevail.api.registry import ModelRegistry
from prevail.api.schemas import (
    AnalyzeRequest, AnalyzeResponse, ExplainRequest, ExplainResponse, FeatureEvidence,
    ForecastRequest, ForecastResponse, ForecastStep,
    HealthResponse, InterventionRequest, InterventionResponse, InterventionStepComparison,
    ModelInfo, RolloutResponse, TemporalEvidence, UploadResponse,
)
from prevail.attack_stage.model import predict_stage_probs
from prevail.common.schema import ATTACK_STAGES
from prevail.explainability.shap_explain import explain_state
from prevail.explainability.temporal import temporal_window_importance
from prevail.intervention import interventions as iv
from prevail.intervention.simulator import (
    build_counterfactual_history, compute_modified_current_state,
    is_out_of_distribution, out_of_distribution_score,
)
from prevail.rollout.rollout import k_step_rollout_batch

registry: ModelRegistry | None = None
store: DatasetStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global registry, store
    registry = ModelRegistry()
    store = DatasetStore()
    yield


app = FastAPI(title="PREVAIL API", version="0.1.0", lifespan=lifespan)

# Explicit origin allowlist -- no "*" (threat-model.md CORS row). Configurable
# via PREVAIL_CORS_ORIGINS (comma-separated) so a non-default dev port (or a
# real deployment host) doesn't require a code change; defaults cover the
# standard local frontend dev/start ports only.
_default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
_extra_origins = [o.strip() for o in os.environ.get("PREVAIL_CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _history_for(dataset_id: str, scenario_id: str, end_window_id: int | None, seq_len: int) -> np.ndarray:
    try:
        ds = store.get(dataset_id)
    except KeyError:
        raise HTTPException(404, f"Unknown dataset_id: {dataset_id}")
    sdf = ds["states"][ds["states"]["scenario_id"] == scenario_id].sort_values("window_id").reset_index(drop=True)
    if len(sdf) == 0:
        raise HTTPException(404, f"Unknown scenario_id: {scenario_id}")
    if end_window_id is None:
        end_window_id = int(sdf["window_id"].max())
    start = end_window_id - seq_len + 1
    hist_df = sdf[(sdf["window_id"] >= start) & (sdf["window_id"] <= end_window_id)]
    if len(hist_df) < seq_len:
        raise HTTPException(400, f"Not enough history before window {end_window_id} for seq_len={seq_len}")
    return hist_df[registry.feature_columns].to_numpy(dtype=float), sdf, end_window_id


@app.get("/api/v1/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", models_loaded=registry is not None)


@app.post("/api/v1/datasets/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)):
    raw_bytes = await file.read()
    try:
        dataset_id = store.ingest_bytes(raw_bytes)
    except IngestionError as e:
        raise HTTPException(400, str(e))
    ds = store.get(dataset_id)
    return UploadResponse(
        dataset_id=dataset_id,
        scenario_ids=store.scenario_ids(dataset_id),
        n_states=len(ds["states"]),
    )


@app.get("/api/v1/datasets/{dataset_id}/scenarios")
def list_scenarios(dataset_id: str):
    try:
        return {"dataset_id": dataset_id, "scenario_ids": store.scenario_ids(dataset_id)}
    except KeyError:
        raise HTTPException(404, f"Unknown dataset_id: {dataset_id}")


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    try:
        ds = store.get(req.dataset_id)
    except KeyError:
        raise HTTPException(404, f"Unknown dataset_id: {req.dataset_id}")
    sdf = ds["states"][ds["states"]["scenario_id"] == req.scenario_id].sort_values("window_id")
    if len(sdf) == 0:
        raise HTTPException(404, f"Unknown scenario_id: {req.scenario_id}")
    latest = sdf.iloc[-1]
    has_true = bool(ds["has_true_attack_stage_labels"])
    return AnalyzeResponse(
        scenario_id=req.scenario_id,
        n_windows=len(sdf),
        latest_window_id=int(latest["window_id"]),
        latest_attack_stage=latest["attack_stage"] if has_true else "Not available",
        latest_attack_label=int(latest["attack_label"]),
        window_size_s=ds["window_size_s"],
        attack_stage_source="true_attack_stage_labels" if has_true else "binary-only (no true stage labels in upload)",
        has_true_attack_stage_labels=has_true,
    )


@app.post("/api/v1/rollout", response_model=RolloutResponse)
def rollout(req: ForecastRequest):
    history, _, _ = _history_for(req.dataset_id, req.scenario_id, req.end_window_id, req.seq_len)
    out = k_step_rollout_batch(registry.world_model, registry.wm_scaler, history[None, :, :], K=req.K)
    return RolloutResponse(
        scenario_id=req.scenario_id, K=req.K,
        predicted_states=out["states"][0].tolist(),
        feature_columns=registry.feature_columns,
    )


@app.post("/api/v1/forecast", response_model=ForecastResponse)
def forecast(req: ForecastRequest):
    history, _, end_window_id = _history_for(req.dataset_id, req.scenario_id, req.end_window_id, req.seq_len)
    out = k_step_rollout_batch(registry.world_model, registry.wm_scaler, history[None, :, :], K=req.K)
    probs = predict_stage_probs(registry.stage_scaler, registry.stage_clf, out["states"][0])

    table = []
    for k in range(req.K):
        stage_idx = int(probs[k].argmax())
        stage = ATTACK_STAGES[stage_idx]
        entry = registry.attack_mapper.lookup(stage)
        table.append(ForecastStep(
            step=k + 1, predicted_stage=stage, stage_probability=float(probs[k, stage_idx]),
            p_attack=float(1.0 - probs[k, ATTACK_STAGES.index("benign")]),
            attck_tactic=entry["tactic"], attck_technique=entry["technique"],
            attck_mapping_confidence=entry["confidence"],
        ))
    return ForecastResponse(scenario_id=req.scenario_id, history_end_window_id=end_window_id, table=table)


_INTERVENTION_BUILDERS = {
    "isolate_host": lambda p: iv.isolate_host(p["host_ip"]),
    "block_source": lambda p: iv.block_source(p["src_ip"]),
    "block_destination_port": lambda p: iv.block_destination_port(int(p["port"])),
    "remove_communication_edge": lambda p: iv.remove_communication_edge(p["ip_a"], p["ip_b"]),
    "segment_asset": lambda p: iv.segment_asset(p["host_ip"], set(p.get("allowed_peers", []))),
    "disable_suspicious_connection": lambda p: iv.disable_suspicious_connection(p["src_ip"], p["dst_ip"], int(p["dst_port"])),
}


@app.post("/api/v1/intervention/simulate", response_model=InterventionResponse)
def simulate_intervention(req: InterventionRequest):
    history, sdf, end_window_id = _history_for(req.dataset_id, req.scenario_id, req.end_window_id, seq_len=10)
    try:
        spec = _INTERVENTION_BUILDERS[req.intervention_type](req.params)
    except KeyError as e:
        raise HTTPException(400, f"Missing required parameter for {req.intervention_type}: {e}")

    ds = store.get(req.dataset_id)
    modified_current = compute_modified_current_state(
        ds["packets"], sdf, end_window_id, ds["window_size_s"], spec, registry.feature_columns,
    )
    counterfactual_history = build_counterfactual_history(history, modified_current)

    def score(hist):
        out = k_step_rollout_batch(registry.world_model, registry.wm_scaler, hist[None, :, :], K=req.K)
        probs = predict_stage_probs(registry.stage_scaler, registry.stage_clf, out["states"][0])
        return 1.0 - probs[:, ATTACK_STAGES.index("benign")]

    p_base = score(history)
    p_cf = score(counterfactual_history)
    ood = out_of_distribution_score(modified_current, registry.wm_scaler.mean_, registry.wm_scaler.std_)

    comparison = [
        InterventionStepComparison(step=k + 1, baseline_p_attack=float(p_base[k]),
                                    counterfactual_p_attack=float(p_cf[k]), delta=float(p_cf[k] - p_base[k]))
        for k in range(req.K)
    ]
    return InterventionResponse(
        scenario_id=req.scenario_id, intervention_name=spec.name, intervention_description=spec.description,
        ood_score=ood, ood_flagged=is_out_of_distribution(modified_current, registry.wm_scaler.mean_, registry.wm_scaler.std_),
        comparison=comparison,
    )


@app.post("/api/v1/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest):
    history, _, _ = _history_for(req.dataset_id, req.scenario_id, req.end_window_id, req.seq_len)
    out = k_step_rollout_batch(registry.world_model, registry.wm_scaler, history[None, :, :], K=1)
    predicted_next_state = out["states"][0, 0]

    probs = predict_stage_probs(registry.stage_scaler, registry.stage_clf, predicted_next_state[None, :])[0]
    predicted_class_idx = int(probs.argmax())
    predicted_stage = ATTACK_STAGES[predicted_class_idx]

    feature_evidence = explain_state(
        registry.stage_scaler, registry.stage_clf, predicted_next_state, registry.feature_columns, predicted_class_idx,
    )
    temporal_evidence = temporal_window_importance(registry.world_model, registry.wm_scaler, history)

    return ExplainResponse(
        scenario_id=req.scenario_id,
        predicted_stage=predicted_stage,
        feature_evidence=[FeatureEvidence(**e) for e in feature_evidence],
        temporal_evidence=[
            TemporalEvidence(label=t["label"], importance_normalized=t["importance_normalized"])
            for t in sorted(temporal_evidence, key=lambda d: -d["importance"])
        ],
        disclaimer=(
            "Evidence shows what the model's prediction is sensitive to. "
            "It is NOT a causal explanation of the underlying network activity."
        ),
    )


@app.get("/api/v1/attack-mapping")
def attack_mapping():
    return {
        "attck_version_referenced": registry.attack_mapper.attck_version_referenced,
        "mappings": registry.attack_mapper.mappings,
    }


@app.get("/api/v1/models", response_model=list[ModelInfo])
def list_models():
    import json
    infos = []
    for name in registry.experiment_dirs():
        with open(registry.artifacts_root / name / "manifest.json") as f:
            infos.append(ModelInfo(name=name, manifest=json.load(f)))
    return infos


@app.get("/api/v1/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    import json
    path = registry.artifacts_root / experiment_id / "manifest.json"
    if not path.exists():
        raise HTTPException(404, f"Unknown experiment_id: {experiment_id}")
    with open(path) as f:
        return json.load(f)
