PYTHON ?= python3
BACKEND_DIR := backend
VENV := $(BACKEND_DIR)/.venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

.PHONY: setup test lint typecheck quality api scan-stm

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install -e '$(BACKEND_DIR)[dev]'

lint:
	cd $(BACKEND_DIR) && .venv/bin/ruff check .

typecheck:
	cd $(BACKEND_DIR) && .venv/bin/mypy app

test:
	cd $(BACKEND_DIR) && .venv/bin/pytest -q

quality: lint typecheck test

api:
	cd $(BACKEND_DIR) && .venv/bin/uvicorn app.main:app --reload

scan-stm:
	cd $(BACKEND_DIR) && .venv/bin/python -m app.cli scan-stm
