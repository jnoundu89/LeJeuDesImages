# Le Jeu Des Images

Company-agnostic team recognition game -- identify colleagues from photos across 19+ game modes. Configurable for any company via `config.yaml` or the `/setup` admin wizard.

## Stack

- **Backend**: Flask, Flask-Babel (i18n), Python 3.10+, pandas, TinyDB, python-dotenv, pyyaml
- **Frontend**: Vanilla JS (`GameEngine` IIFE), CSS3 (animations, glassmorphism, responsive)
- **Data**: CSV (configurable path), TinyDB (`scores_db.json`)
- **Config**: `config.yaml` (company branding + CSV column mapping)
- **Deploy**: Docker (`docker compose up`)

## Project Structure

```
app.py                  # Flask entry point, auto-discovery, Babel, context processor
config.yaml             # Company config: branding + CSV column mapping
config.example.yaml     # Reference config for new deployments
Dockerfile / docker-compose.yml
models/
  config.py             # CompanyConfig -- loads/saves config.yaml
  employee.py           # EmployeeData -- CSV with column normalization at load time
  score.py              # ScoreManager -- TinyDB, per-mode scores, flexible stats
  game.py               # GameManager -- core game orchestration
  game_mode.py          # GameMode ABC + helpers + NormalMode + ReverseMode + Factory
  *_mode.py             # 18+ concrete game modes (auto-discovered)
routes/
  game_routes.py        # Main game routes (generic /check via mode.handle_answer)
  card_game_routes.py   # Card game API blueprint
  admin_routes.py       # /setup wizard (CSV upload, column mapping, photo upload)
templates/
  base.html             # Root template
  base_page.html        # Pages: header, footer, music player, particles
  base_game.html        # Game modes: 3-column layout, stats, timer, form
  setup.html            # Admin setup wizard (4 steps)
  *.html                # 30 templates using {% extends %}
static/
  game-engine.js        # GameEngine IIFE (checkAnswer, timer, confetti, progress)
  scripts.js            # Thin wrappers -> GameEngine
  ...
translations/           # Flask-Babel FR/EN catalogs (227 strings)
tests/                  # 65 pytest tests (88% coverage on core modules)
tools/
  validate_data.py      # CLI: validate CSV + photos against config
  importers/lucca/      # Reference Lucca HR API importer
docs/
  data-format.md        # CSV format documentation
```

## Setup for a new company

### Option A: Admin wizard
1. `docker compose up` (or `python app.py`)
2. Go to `/setup`
3. Fill in company branding, upload CSV, map columns, upload photos
4. Save

### Option B: Manual config
1. Copy `config.example.yaml` to `config.yaml`
2. Set company name, logo URL, contact email
3. Place employee CSV and adjust `data.column_mapping`
4. Place photos in the configured `images_dir`
5. Run `python tools/validate_data.py` to verify
6. Run `python app.py`

## Canonical employee fields

All code uses these canonical names (mapped from CSV columns in `config.yaml`):

| Canonical | Description | Required |
|-----------|-------------|----------|
| `first_name` | First name | Yes |
| `last_name` | Last name | Yes |
| `photo` | Path to photo | Yes |
| `team` | Department / team | Yes |
| `job_title` | Job title | Yes |
| `company` | Legal entity / company | Yes |
| `sex` | Gender (for choice filtering) | Yes |
| `birth_date` | Birth date (ISO format) | No (age mode) |
| `contract_start` | Contract start date | No (seniority mode) |
| `manager_name` | Manager name | No (manager/clue modes) |

## Running

```bash
# Local
cp .env.example .env  # Edit SECRET_KEY, FLASK_DEBUG, ADMIN_PASSWORD
python app.py          # -> http://127.0.0.1:5000

# Docker
docker compose up      # -> http://localhost:5000

# Tests
make test              # or: uv run --extra dev pytest tests/ -v

# Lint
make lint              # or: uv run --extra dev ruff check .

# i18n
make babel-extract     # Extract new strings
make babel-compile     # Compile catalogs after editing .po files
```

## Architecture

- **Auto-discovery**: `pkgutil.iter_modules` scans `models/*_mode.py` for `GameMode` subclasses
- **GameMode helpers**: `_pick_next_employee()`, `_get_name_choices()`, `_make_full_name()`, `handle_answer()`
- **Generic routes**: `/check` delegates to `mode.handle_answer(user_id, form, session)` -- no if-elif per mode
- **Template inheritance**: `base.html` -> `base_page.html` / `base_game.html` -> 30 child templates
- **Config-driven**: `CompanyConfig` loads branding + column mapping; `EmployeeData` normalizes CSV at load time
- **i18n**: Flask-Babel with cookie-based locale selection (FR/EN), `_()` in templates, `_l()` in Python
- **Scores**: per-mode tracking, flexible `stat_updates` dict, optional `player_name`
