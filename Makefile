PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip

.PHONY: setup test coverage etl etl-public api dq clean compile

setup:
	python3.11 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

coverage:
	$(PYTHON) -m pytest --cov=src --cov-report=term-missing

compile:
	$(PYTHON) -m compileall -q src tests

etl:
	$(PYTHON) -m src.etl.run_pipeline

etl-public:
	$(PYTHON) -m src.etl.run_pipeline --refresh-public

api:
	$(PYTHON) -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

dq:
	$(PYTHON) -c "from src.db import get_engine, initialize_database; from src.quality.checks import run_data_quality; e=get_engine(); initialize_database(e); print(run_data_quality(e))"

clean:
	rm -f data/*.duckdb data/*.duckdb.wal
	find outputs -type f ! -name '.gitkeep' -delete
