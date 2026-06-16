SHELL := /bin/bash

PYTHON := .venv/bin/python
PYTEST := .venv/bin/pytest
RUFF := .venv/bin/ruff
UVICORN := .venv/bin/uvicorn
ALEMBIC := .venv/bin/alembic
POETRY := poetry
COMPOSE_FILE := docker-compose.yml

.DEFAULT_GOAL := help

.PHONY: help install run test lint import-check check migrate downgrade revision db-up db-down db-logs clean

help:
	@echo "[make:help] Available commands:"
	@echo "  [make:install]       Install project dependencies with Poetry"
	@echo "  [make:run]           Run the FastAPI development server"
	@echo "  [make:test]          Run pytest"
	@echo "  [make:lint]          Run Ruff checks"
	@echo "  [make:import-check]  Verify src.main imports"
	@echo "  [make:check]         Run tests, lint, and import check"
	@echo "  [make:migrate]       Apply Alembic migrations"
	@echo "  [make:downgrade]     Roll back one Alembic migration"
	@echo "  [make:revision]      Create an Alembic migration: make revision name=\"describe change\""
	@echo "  [make:db-up]         Start Docker Compose services"
	@echo "  [make:db-down]       Stop Docker Compose services"
	@echo "  [make:db-logs]       Follow Docker Compose logs"
	@echo "  [make:clean]         Remove local Python cache files"

install:
	@echo "[make:install] Installing dependencies with Poetry"
	@$(POETRY) install

run:
	@echo "[make:run] Starting FastAPI development server on http://localhost:8000"
	@$(UVICORN) src.main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "[make:test] Running pytest"
	@$(PYTEST) -q

lint:
	@echo "[make:lint] Running Ruff checks"
	@$(RUFF) check src tests

import-check:
	@echo "[make:import-check] Verifying src.main imports"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -c "import src.main; print('import ok')"

check: test lint import-check
	@echo "[make:check] All checks completed"

migrate:
	@echo "[make:migrate] Applying Alembic migrations"
	@$(ALEMBIC) upgrade head

downgrade:
	@echo "[make:downgrade] Rolling back one Alembic migration"
	@$(ALEMBIC) downgrade -1

revision:
	@if [ -z "$(name)" ]; then \
		echo "[make:revision] Usage: make revision name=\"describe change\""; \
		exit 1; \
	fi
	@echo "[make:revision] Creating Alembic migration: $(name)"
	@$(ALEMBIC) revision --autogenerate -m "$(name)"

db-up:
	@echo "[make:db-up] Starting Docker Compose services"
	@docker compose -f $(COMPOSE_FILE) up -d

db-down:
	@echo "[make:db-down] Stopping Docker Compose services"
	@docker compose -f $(COMPOSE_FILE) down

db-logs:
	@echo "[make:db-logs] Following Docker Compose logs"
	@docker compose -f $(COMPOSE_FILE) logs -f

clean:
	@echo "[make:clean] Removing local Python cache files"
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +
