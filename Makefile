.PHONY: setup test lint pipeline baseline worldmodel api frontend offline-test

VENV=.venv/bin

setup:
	python3 -m venv .venv
	$(VENV)/pip install --upgrade pip
	$(VENV)/pip install -e ".[dev]"

test:
	$(VENV)/pytest -q

pipeline:
	$(VENV)/python -m prevail.scripts.run_pipeline

baseline:
	$(VENV)/python -m prevail.baselines.train

worldmodel:
	$(VENV)/python -m prevail.world_model.train

api:
	$(VENV)/uvicorn prevail.api.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

offline-test:
	bash scripts/offline_smoke_test.sh
