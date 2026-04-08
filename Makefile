.PHONY: run test lint format validate-data install

install:
	uv sync --extra dev

run:
	uv run python app.py

test:
	uv run --extra dev pytest tests/ -v

lint:
	uv run --extra dev ruff check .

format:
	uv run --extra dev ruff format .

validate-data:
	uv run python tools/validate_data.py
