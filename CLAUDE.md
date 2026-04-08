# Le Jeu Des Images

Company-agnostic team recognition game -- identify colleagues from photos across 19+ game modes. Configurable for any company via `config.yaml`.

## Stack

- **Backend**: Flask, Python 3.10+, pandas, TinyDB, python-dotenv, pyyaml
- **Frontend**: Vanilla JS, CSS3 (animations, glassmorphism, responsive)
- **Data**: CSV (configurable path), TinyDB (`scores_db.json`)
- **Config**: `config.yaml` (company branding + CSV column mapping)

## Project Structure

```
app.py                  # Flask entry point, mode registration, server start
config.yaml             # Company config: branding + CSV column mapping
config.example.yaml     # Reference config for new deployments
models/                 # Game logic
  config.py             # CompanyConfig -- loads config.yaml
  employee.py           # EmployeeData -- CSV data access with column normalization
  score.py              # ScoreManager -- TinyDB persistence
  game.py               # GameManager -- core game orchestration
  game_mode.py          # Abstract GameMode + GameModeFactory
  *_mode.py             # 18+ concrete game mode implementations
routes/
  game_routes.py        # Main game routes
  card_game_routes.py   # Card game blueprint
templates/              # 31 Jinja2 templates
static/                 # CSS, JS, images, data
tests/                  # pytest test suite
```

## Setup for a new company

1. Copy `config.example.yaml` to `config.yaml`
2. Set company name, logo URL, contact email
3. Place employee CSV and adjust `data.column_mapping` to match your CSV columns
4. Place employee photos in the configured `images_dir`
5. Run `python app.py`

## Canonical employee fields

All code uses these canonical names (mapped from CSV columns in `config.yaml`):

| Canonical | Description |
|-----------|-------------|
| `first_name` | First name |
| `last_name` | Last name |
| `photo` | Path to photo |
| `team` | Department / team |
| `job_title` | Job title |
| `company` | Legal entity / company |
| `sex` | Gender (for choice filtering) |
| `birth_date` | Birth date (optional) |
| `contract_start` | Contract start date (optional) |
| `manager_name` | Manager name (optional) |

## Running

```bash
cp .env.example .env  # Edit SECRET_KEY and FLASK_DEBUG
python app.py
# -> http://127.0.0.1:5000
```

## Testing

```bash
uv run --extra dev pytest tests/ -v
```

## Architecture

- **Factory**: `GameModeFactory` registers/retrieves game modes
- **Strategy**: `GameMode` ABC, each mode implements `initialize()`, `get_question_data()`, `update_score()`
- **Config-driven**: `CompanyConfig` loads branding + column mapping; `EmployeeData` normalizes CSV at load time
- **Context processor**: Jinja2 templates receive `company_name`, `company_logo_url`, `company_tagline`, `company_email`

## Notes

- All UI text is in French
- Scores persisted in `scores_db.json` (gitignored)
- Secret key loaded from `SECRET_KEY` env var (no more hardcoded secret)
