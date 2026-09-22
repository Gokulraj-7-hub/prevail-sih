from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    dataset_id: str
    scenario_ids: list[str]
    n_states: int


class DatasetProfile(BaseModel):
    """Honest structural report derived ONLY from the columns/label/timestamp
    signal actually present in the uploaded file. Nothing here is inferred,
    fabricated, or about model output."""

    dataset_id: str
    n_rows: int
    n_columns: int
    filename: str
    timestamp_column: Optional[str] = None
    has_timestamp: bool
    temporal_order_available: bool
    timestamp_range: Optional[list[str]] = None
    feature_columns: list[str]
    n_numeric_features: int
    n_categorical_features: int
    label_column: Optional[str] = None
    has_label: bool
    label_cardinality: Optional[int] = None
    label_values: Optional[list[str]] = None
    is_binary_label: bool = False
    has_true_attack_stage_labels: bool = False
    attack_stage_source: str = "unavailable"
    compatible: bool
    warnings: list[str]


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
    # Honesty gate (spec S14/S19 + DECISIONS.md D-013): "unavailable" when the
    # uploaded telemetry carried only binary attack labels (no true
    # attack-stage ground-truth). NEVER emits a fabricated "benign" stage from
    # _window_attack_stage's absence fallback for binary-only uploads.
    attack_stage_source: str
    has_true_attack_stage_labels: bool
    # Honesty provenance for the stage claim above (spec S14/S19 + DECISIONS.md
    # D-013). "true_true_attack_stage_labels" = real stage ground-truth was
    # present in the uploaded telemetry. "binary_label_only" = the upload only
    # carried a binary label, so there is NO true stage; "Not available" here
    # must never be reported as if it were an observed stage.
    attack_stage_source: str
    has_true_attack_stage_labels: bool


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


class ExplainRequest(BaseModel):
    dataset_id: str
    scenario_id: str
    end_window_id: Optional[int] = None
    seq_len: int = Field(10, ge=1, le=50)


class FeatureEvidence(BaseModel):
    feature: str
    shap_value: float
    direction: str


class TemporalEvidence(BaseModel):
    label: str
    importance_normalized: float


class ExplainResponse(BaseModel):
    scenario_id: str
    predicted_stage: str
    feature_evidence: list[FeatureEvidence]
    temporal_evidence: list[TemporalEvidence]
    disclaimer: str


class ModelInfo(BaseModel):
    name: str
    manifest: dict


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
