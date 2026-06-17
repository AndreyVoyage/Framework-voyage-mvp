# Voyage Framework — Makefile
.PHONY: install test test-cov lint format fix clean docs run-dev badge ci-test ci-lint ci-coverage release

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

badge:
	coverage-badge -o coverage.svg -f

ci-test:
	pytest tests/ -q --tb=short

ci-lint:
	ruff check voyage_framework
	mypy voyage_framework

ci-coverage:
	pytest --cov=voyage_framework --cov-report=xml --cov-report=html
	coverage-badge -o coverage.svg -f

release:
	python -m build
	twine upload dist/*
