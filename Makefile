.PHONY: install generate-data validate-data test lint run demo cdf-deploy cdf-ingest clean-demo

install:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

generate-data:
	python scripts/01_generate_sample_data.py

validate-data:
	python scripts/02_validate_sample_data.py

test:
	pytest

lint:
	ruff check .
	ruff format --check .

run:
	streamlit run app/Home.py

demo: generate-data validate-data run

cdf-deploy:
	python scripts/03_deploy_cdf_resources.py

cdf-ingest: generate-data
	python scripts/04_ingest_master_data.py
	python scripts/05_ingest_time_series.py
	python scripts/06_ingest_work_orders.py
	python scripts/07_ingest_documents.py
	python scripts/08_run_detection.py
	python scripts/09_create_investigations.py
	python scripts/10_verify_deployment.py

clean-demo:
	python scripts/cleanup_demo_resources.py
