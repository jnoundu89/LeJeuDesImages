.PHONY: run test test-e2e lint format validate-data install babel-extract babel-init babel-update babel-compile typecheck

install:
	uv sync --extra dev

run:
	uv run python app.py

test:
	APP_CONFIG=tests/fixtures/test_config.yaml uv run --extra dev pytest tests/ -v -m "not e2e"

test-e2e:
	uv run pytest tests/test_e2e.py -v -m e2e

typecheck:
	uv run --extra dev pyright models/ routes/

lint:
	uv run --extra dev ruff check .

format:
	uv run --extra dev ruff format .

validate-data:
	uv run python tools/validate_data.py

babel-extract:
	uv run pybabel extract -F babel.cfg -k _l -o translations/messages.pot .

babel-init:
	uv run pybabel init -i translations/messages.pot -d translations -l en
	uv run pybabel init -i translations/messages.pot -d translations -l fr

babel-update:
	uv run pybabel update -i translations/messages.pot -d translations

babel-compile:
	uv run pybabel compile -d translations
