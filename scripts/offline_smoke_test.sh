#!/usr/bin/env bash
# Offline smoke test (Phase 21): start application -> load sample telemetry
# -> forecast -> dashboard works. See docs/architecture/offline-verification.md
# for what this does and does not prove about network isolation.
set -euo pipefail
cd "$(dirname "$0")/.."

API_PORT="${PREVAIL_API_PORT:-8000}"
FRONTEND_PORT="${PREVAIL_FRONTEND_PORT:-3000}"

echo "== Building images =="
docker compose build

echo "== Starting stack =="
docker compose up -d

cleanup() { echo "== Tearing down =="; docker compose down; }
trap cleanup EXIT

echo "== Waiting for API health =="
for i in $(seq 1 30); do
  if curl -sf http://localhost:${API_PORT}/api/v1/health > /dev/null; then
    echo "API healthy after ${i}s"
    break
  fi
  sleep 1
done
curl -sf http://localhost:${API_PORT}/api/v1/health | grep -q '"models_loaded":true' \
  || { echo "FAIL: models not loaded"; exit 1; }

echo "== Loading sample telemetry (demo dataset) =="
curl -sf -X POST http://localhost:${API_PORT}/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"dataset_id":"demo","scenario_id":"scn_009_attack"}' | grep -q '"n_windows":60' \
  || { echo "FAIL: analyze did not return expected demo scenario"; exit 1; }

echo "== Running forecast =="
curl -sf -X POST http://localhost:${API_PORT}/api/v1/forecast \
  -H "Content-Type: application/json" \
  -d '{"dataset_id":"demo","scenario_id":"scn_009_attack","end_window_id":21,"K":5,"seq_len":10}' \
  | grep -q '"predicted_stage"' \
  || { echo "FAIL: forecast did not return a prediction"; exit 1; }

echo "== Checking dashboard renders =="
for i in $(seq 1 30); do
  if curl -sf http://localhost:${FRONTEND_PORT}/ | grep -q "PREVAIL"; then
    echo "Dashboard OK after ${i}s"
    break
  fi
  sleep 1
done
curl -sf http://localhost:${FRONTEND_PORT}/ | grep -q "PREVAIL" || { echo "FAIL: dashboard did not render"; exit 1; }

echo "== ALL CHECKS PASSED =="
