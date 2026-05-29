# Voyage Framework — Makefile
.PHONY: install test lint format clean docs

install:
	pip install -e ".[dev]"

test:
	pytest -v

test-cov:
	pytest --cov=voyage_framework --cov-report=html --cov-report=term

lint:
	mypy voyage_framework
	ruff check voyage_framework

format:
	ruff format voyage_framework

fix:
	ruff check --fix voyage_framework

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage .voyage

docs:
	@echo "Documentation: https://github.com/AndreyVoyage/Framework-voyage-v2"

run-dev:
	voyage status
