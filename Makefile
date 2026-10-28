.PHONY: install test lint format typecheck security build run clean ci

install:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest -q

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy src/

security:
	bandit -r src/ -x tests/ -ll
	pip-audit

build:
	docker build -t prime-agent:latest .

run:
	prime-agent "check if zachara.dev is up"

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__ .coverage htmlcov

ci: lint typecheck test security
	@echo "All checks passed"
