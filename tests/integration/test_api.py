"""Integration test: dataset -> preprocessing -> state -> model -> rollout,
exercised through the actual FastAPI app (master prompt Phase 26 integration
test shape), using fastapi.testclient so no real server/port is needed.

Requires trained artifacts under artifacts/ (run scripts/train_baseline.py,
scripts/train_world_model.py, scripts/train_attack_stage.py first) -- skipped
otherwise so `pytest` stays runnable before those are trained.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_PRESENT = (ROOT / "artifacts" / "world_model" / "world_model_v1.pt").exists()

pytestmark = pytest.mark.skipif(not ARTIFACTS_PRESENT, reason="trained artifacts not present; run scripts/train_*.py first")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from prevail.api.main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["models_loaded"] is True


def test_analyze_demo_scenario(client):
    r = client.post("/api/v1/analyze", json={"dataset_id": "demo", "scenario_id": "scn_009_attack"})
    assert r.status_code == 200
    body = r.json()
    assert body["n_windows"] == 60


def test_analyze_unknown_dataset_404(client):
    r = client.post("/api/v1/analyze", json={"dataset_id": "nope", "scenario_id": "x"})
    assert r.status_code == 404


def test_forecast_probabilities_in_unit_interval(client):
    r = client.post("/api/v1/forecast", json={
        "dataset_id": "demo", "scenario_id": "scn_009_attack", "end_window_id": 21, "K": 5, "seq_len": 10,
    })
    assert r.status_code == 200
    table = r.json()["table"]
    assert len(table) == 5
    for step in table:
        assert 0.0 <= step["p_attack"] <= 1.0
        assert 0.0 <= step["stage_probability"] <= 1.0


def test_intervention_missing_param_400(client):
    r = client.post("/api/v1/intervention/simulate", json={
        "dataset_id": "demo", "scenario_id": "scn_009_attack", "end_window_id": 21, "K": 3,
        "intervention_type": "isolate_host", "params": {},
    })
    assert r.status_code == 400


def test_intervention_response_shape(client):
    r = client.post("/api/v1/intervention/simulate", json={
        "dataset_id": "demo", "scenario_id": "scn_009_attack", "end_window_id": 21, "K": 3,
        "intervention_type": "block_destination_port", "params": {"port": 8080},
    })
    assert r.status_code == 200
    body = r.json()
    assert len(body["comparison"]) == 3
    assert "NOT a causal claim" in body["disclaimer"]
