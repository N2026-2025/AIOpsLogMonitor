.PHONY: install test lint seed train serve clean

install:
	pip install -r requirements.txt
	pip install pytest flake8

test:
	pytest tests/ -v

lint:
	flake8 src/ --max-line-length=120

seed:
	python scripts/seed_deterministic.py

train:
	python -m src.ml.train

serve:
	python -m src.api.main

clean:
	rm -rf .pytest_cache __pycache__ src/**/__pycache__ tests/**/__pycache__
