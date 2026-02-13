# SPDX-License-Identifier: CC-BY-SA-4.0

.PHONY: dev test cov lint format check run clean

PYTHONPATH := src
export PYTHONPATH

dev:
	poetry install

test:
	poetry run pytest

cov:
	poetry run pytest --cov=bot --cov-report=term-missing --cov-report=html

lint:
	poetry run ruff format --check src tests
	poetry run ruff check src tests
	poetry run mypy src --ignore-missing-imports

format:
	poetry run ruff format src tests
	poetry run ruff check --fix src tests

check: lint test

run:
	poetry run python -m bot.main

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
