# =============================================================================
# DEDAN Health — developer entry points
#
# Run `make help` for the available targets. Every target here is wired to a
# command that actually works in this repository.
# =============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

VENV        := .venv
PY          := $(VENV)/bin/python
BACKEND_DIR := backend-v2
FRONT_DIR   := web-portal
RUN_DIR     := .run

BACKEND_PORT  ?= 8001
FRONTEND_PORT ?= 3000

export BACKEND_PORT FRONTEND_PORT

.PHONY: help setup setup-backend setup-frontend run run-backend run-frontend \
        stop test test-backend test-frontend test-system lint format fmt-check \
        health clean build

## ---------------------------------------------------------------------------
## Help
## ---------------------------------------------------------------------------
help: ## Show this help
	@echo "DEDAN Health — available targets"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "  Web portal : http://localhost:$(FRONTEND_PORT)"
	@echo "  API        : http://localhost:$(BACKEND_PORT)"

## ---------------------------------------------------------------------------
## Setup
## ---------------------------------------------------------------------------
setup: setup-backend setup-frontend ## Install all dependencies

setup-backend: ## Create the venv and install backend dependencies
	@if [ ! -d "$(VENV)" ]; then \
		echo ">> Creating virtualenv"; python3 -m venv $(VENV); \
	fi
	@echo ">> Installing backend dependencies"
	@$(PY) -m pip install --quiet --upgrade pip || true
	@$(PY) -m pip install --quiet -r $(BACKEND_DIR)/requirements.txt
	@if [ ! -f $(BACKEND_DIR)/.env ]; then \
		cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env; \
		echo ">> Created $(BACKEND_DIR)/.env"; \
	fi
	@echo ">> Backend ready"

setup-frontend: ## Install frontend dependencies
	@echo ">> Installing frontend dependencies"
	@cd $(FRONT_DIR) && npm install --no-audit --no-fund
	@echo ">> Frontend ready"

## ---------------------------------------------------------------------------
## Run
## ---------------------------------------------------------------------------
run: ## Set up if needed, then start backend and frontend
	@./scripts/setup-and-run.sh

run-backend: ## Run the API in the foreground (offline mode)
	@cd $(BACKEND_DIR) && AI_PROVIDER_MODE=offline ../$(VENV)/bin/python -m uvicorn \
		main_clinical:app --host 0.0.0.0 --port $(BACKEND_PORT)

run-frontend: ## Run the web portal in the foreground
	@cd $(FRONT_DIR) && npm run dev -- --port $(FRONTEND_PORT)

stop: ## Stop the DEDAN services
	@./scripts/stop.sh

## ---------------------------------------------------------------------------
## Test
## ---------------------------------------------------------------------------
test: test-backend test-frontend ## Run all automated tests

test-backend: ## Run the Python test suite
	@cd $(BACKEND_DIR) && ../$(VENV)/bin/python -m pytest tests/ -v --no-header -p no:warnings

test-frontend: ## Run the frontend test suite
	@cd $(FRONT_DIR) && npm test

test-system: ## Run the end-to-end system smoke test
	@./scripts/test-system.sh

## ---------------------------------------------------------------------------
## Quality
## ---------------------------------------------------------------------------
lint: ## Type-check the frontend and byte-compile the backend
	@echo ">> TypeScript"
	@cd $(FRONT_DIR) && npx tsc --noEmit
	@echo ">> Python syntax"
	@cd $(BACKEND_DIR) && ../$(VENV)/bin/python -m compileall -q \
		main_clinical.py app providers models tests > /dev/null
	@echo "Lint OK"

format: ## Normalise whitespace and final newlines in tracked source
	@find . -type f \
		-not -path './.git/*' -not -path './node_modules/*' -not -path './.venv/*' \
		-not -path './venv/*' -not -path '*/venv/*' -not -path '*/__pycache__/*' \
		-not -path './web-portal/dist/*' -not -path './web-portal/node_modules/*' \
		-not -name '*.png' -not -name '*.jpg' -not -name '*.jpeg' -not -name '*.ico' \
		-not -name '*.db' -not -name 'package-lock.json' \
		-exec sed -i -e 's/[[:space:]]*$$//' -e 's/\r$$//' {} +
	@echo "Format complete"

fmt-check: ## Verify whitespace normalisation (no files modified)
	@bash scripts/check-format.sh

## ---------------------------------------------------------------------------
## Operations
## ---------------------------------------------------------------------------
health: ## Check that the running system is healthy
	@./scripts/health-check.sh

build: ## Build the frontend for production
	@cd $(FRONT_DIR) && npm run build

clean: ## Remove caches, build output and runtime state
	@echo ">> Removing caches and build output"
	@rm -rf $(FRONT_DIR)/dist $(FRONT_DIR)/coverage $(FRONT_DIR)/.vite
	@rm -rf $(RUN_DIR)
	@find . -type d -name __pycache__ -not -path './.venv/*' -not -path './venv/*' \
		-not -path '*/venv/*' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -not -path './.venv/*' -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -not -path './.venv/*' -delete 2>/dev/null || true
	@echo "Clean complete"
