.PHONY: help up down migrate seed datagen test lint eval-extraction eval-agent train-smoke export-corrections compare-candidate bench demo

help:
	@echo "DocuMind CLI Tasks:"
	@echo "  make up                 Start local services in docker compose"
	@echo "  make down               Stop docker compose services"
	@echo "  make migrate            Apply Alembic migrations"
	@echo "  make seed               Seed sample workspace and user data"
	@echo "  make datagen            Generate synthetic Indian business documents"
	@echo "  make test               Run unit, property and integration tests"
	@echo "  make lint               Run ruff and mypy checks"
	@echo "  make eval-extraction    Run extraction benchmark on configured backend"
	@echo "  make eval-agent         Run text-to-SQL and RAG agent evaluation"
	@echo "  make train-smoke        Smoke test QLoRA training script locally on CPU"
	@echo "  make export-corrections Export verified human edits to JSONL dataset"
	@echo "  make compare-candidate  Compare candidate model to champion in MLflow"
	@echo "  make bench              Benchmark serving throughput and latency"
	@echo "  make demo               Launch demo Streamlit UI"

up:
	docker compose up -d

down:
	docker compose down

migrate:
	alembic upgrade head

seed:
	python3 -m scripts.seed_demo_data

datagen:
	python3 -m datagen.cli --count 1500 --seed 42

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/
	mypy src/

eval-extraction:
	python3 -m eval.run_extraction_eval --backend $(or $(MODEL),stub)

eval-agent:
	python3 -m eval.run_agent_eval

train-smoke:
	python3 -m training.train_qlora --smoke-test --output-dir /tmp/qlora-smoke

export-corrections:
	python3 -m documind.flywheel.export

compare-candidate:
	python3 -m eval.compare_candidate

bench:
	python3 -m eval.bench_serving

demo:
	streamlit run ui/app.py
