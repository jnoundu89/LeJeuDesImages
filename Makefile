.PHONY: run run-dev test test-e2e lint format validate-data install babel-extract babel-init babel-update babel-compile typecheck demo-dataset

install:
	uv sync --extra dev

run:
	uv run python app.py

# Same as `run` but with Flask debug + Jinja template auto-reload, so edits
# to templates show up on the next request without restarting. Use this for
# CSS / template iteration; use plain `make run` for production-like checks.
run-dev:
	FLASK_DEBUG=true uv run python app.py

# Populate data/demo/ with the bundled sample CSV and avatars so the app
# is playable out of the box without going through the /setup wizard.
demo-dataset:
	mkdir -p data/demo/photos
	cp demo/team.csv data/demo/team.csv
	cp demo/photos/*.png data/demo/photos/
	@echo "Demo dataset installed under data/demo/."
	@echo "Point config.yaml (or the /setup wizard) at csv_path: data/demo/team.csv and images_dir: data/demo/photos."

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
