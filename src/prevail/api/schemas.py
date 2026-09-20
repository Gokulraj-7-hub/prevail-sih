from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    dataset_id: str
    scenario_ids: list[str]
    n_states: int


class AnalyzeRequest(BaseModel):
    dataset_id: str
    scenario_id: str


class AnalyzeResponse(BaseModel):
    scenario_id: str
    n_windows: int
    latest_window_id: int
    latest_attack_stage: str
    latest_attack_label: int
    window_size_s: float


class ForecastRequest(BaseModel):
    dataset_id: str
    scenario_id: str
    end_window_id: Optional[int] = Field(None, description="History ends here; default = last available window")
    K: int = Field(5, ge=1, le=10)
    seq_len: int = Field(10, ge=1, le=50)


class ForecastStep(BaseModel):
    step: int
    predicted_stage: str
    stage_probability: float
    p_attack: float
    attck_tactic: Optional[dict]
    attck_technique: Optional[dict]
    attck_mapping_confidence: str


class ForecastResponse(BaseModel):
    scenario_id: str
    history_end_window_id: int
    table: list[ForecastStep]


class RolloutResponse(BaseModel):
    scenario_id: str
    K: int
    predicted_states: list[list[float]]
    feature_columns: list[str]


InterventionType = Literal[
    "isolate_host", "block_source", "block_destination_port",
    "remove_communication_edge", "segment_asset", "disable_suspicious_connection",
]


class InterventionRequest(BaseModel):
    dataset_id: str
    scenario_id: str
    end_window_id: Optional[int] = None
    K: int = Field(5, ge=1, le=10)
    intervention_type: InterventionType
    params: dict = Field(default_factory=dict)


class InterventionStepComparison(BaseModel):
    step: int
    baseline_p_attack: float
    counterfactual_p_attack: float
    delta: float


class InterventionResponse(BaseModel):
    scenario_id: str
    intervention_name: str
    intervention_description: str
    ood_score: float
    ood_flagged: bool
    comparison: list[InterventionStepComparison]
    disclaimer: str = (
        "The model forecasts a probability change under this simulated intervention. "
        "This is NOT a causal claim that the intervention would prevent the attack in reality."
    )


class ModelInfo(BaseModel):
    name: str
    manifest: dict


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
