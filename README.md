# Le Jeu Des Images

A company-agnostic team recognition game -- identify your colleagues from photos across 22 game modes. Register **multiple datasets** (one per company) from the browser and switch between them at runtime; no YAML editing required.

![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen)
![Flask](https://img.shields.io/badge/Flask-2.3%2B-orange)
![i18n](https://img.shields.io/badge/i18n-FR%20%7C%20EN-blue)
![Docker](https://img.shields.io/badge/Docker-ready-blue)

## Quick Start

### Option A: Docker

```bash
docker compose up
# -> http://localhost:5000
# -> http://localhost:5000/setup  (admin wizard)
```

### Option B: Local

```bash
uv sync

cp .env.example .env        # Edit SECRET_KEY, ADMIN_PASSWORD
uv run python app.py
# -> http://127.0.0.1:5000  (redirects to /setup on first run)
```

The app boots without any `config.yaml`. On first launch every route redirects to `/setup` where the wizard walks you through creating your first dataset. See `DEPLOY.md` for the full flow.

## Setup for a New Company

Each company lives as an independent **dataset**: CSV + photos + branding, all configurable through `/setup`.

1. Go to `/setup` → *Ajouter un dataset*
2. Wizard:
   - Step 1: pick a dataset id + company branding (name, logo, tagline)
   - Step 2: upload your CSV, map columns to the game's canonical fields (`first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`, + optional `birth_date`, `contract_start`, `manager_name`)
   - Step 3: upload photos (ZIP) — optional at create time; can be done later
   - Step 4: review + save
3. Dataset is hot-registered — no restart. Switch via the header dropdown.
4. Per-employee edits (rename, replace photo, delete) available from *Employés* on the dataset card.

See [docs/data-format.md](docs/data-format.md) for the CSV specification.

Validate your setup:
```bash
uv run python tools/validate_data.py
```

## Game Modes

### Classic
- **Normal** -- Identify company, team, name, and position from a photo
- **Reverse** -- Identify the person from a name
- **Pixelation** -- Progressively clearer image
- **Timed** -- Decreasing time per question
- **Team** -- Identify all members of a team
- **Quiz** -- Answer questions about colleagues

### Advanced
- **Clue** -- Progressive hints
- **Memory** -- Card matching game
- **Speed** -- Max identifications in a time limit
- **Team Guess** -- Guess which team someone belongs to
- **Missing Person** -- Find the missing person
- **Position Match** -- Match people to positions
- **Progressive Hint** -- Hints gradually revealed
- **Manager** -- Identify someone's manager
- **Seniority** -- Guess years of seniority
- **Age** -- Guess someone's age

### Creative
- **Scrambled Face** -- Facial features mixed from multiple people
- **Emoji Challenge** -- Identify from emoji clues
- **Silhouette** -- Black silhouettes only
- **Mirror** -- Horizontally flipped images

### Special
- **Card Game** -- Strategic card battle
- **ARR** -- Hidden arcade racing game (Konami code: up up down down left right left right B A)

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests (65 tests, 88% coverage on core modules)
make test

# Lint
make lint

# Format
make format

# Validate employee data
make validate-data

# i18n: extract new strings after code changes
make babel-extract
make babel-compile
```

## Architecture

```
app.py                     # Entry point — builds DatasetRegistry, registers blueprints
config.yaml                # app-level settings + datasets registry (gitignored)
models/
  config.py                # AppConfig + DatasetConfig (+ CompanyConfig back-compat)
  dataset.py               # Dataset — bundles EmployeeData/ScoreManager/GameManager per id
  dataset_registry.py      # Runtime registry, cookie-based resolution
  employee.py              # Employee(dict) + EmployeeData (CSV load + CRUD + save)
  score.py                 # ScoreManager (per-dataset TinyDB)
  game.py                  # GameManager (core orchestration)
  game_mode.py             # GameMode ABC + helpers + Factory
  *_mode.py                # 22 game modes (auto-discovered per dataset)
routes/
  game_routes.py           # Per-request dataset resolution
  card_game_routes.py      # Card game API
  admin_routes.py          # /setup datasets + employees CRUD
templates/
  base.html → base_page.html / base_game.html
  _switchers.html          # Header partial (language + dataset dropdown)
  setup_list.html          # Datasets landing
  setup_wizard.html        # Add / edit dataset wizard
  employees_list.html      # Per-dataset employees
  employee_edit.html       # Per-employee form
data/<dataset_id>/         # Per-dataset CSV + photos + scores (all gitignored)
translations/              # Flask-Babel FR/EN
tests/                     # pytest — unit, integration, E2E (Playwright)
tools/validate_data.py     # CSV + photo validation CLI
docs/data-format.md        # CSV format documentation
```

### Key Design Decisions

- **Multi-dataset runtime**: N datasets loaded simultaneously, switched per request via the `dataset` cookie. Scores, branding, data all isolated. No restart to add/remove datasets.
- **Legacy config auto-migration**: old single-dataset `config.yaml` is silently promoted to a single dataset named `default`.
- **Company-agnostic**: All company data lives in `config.yaml` + `data/` (gitignored). Zero hardcoded references in code.
- **Auto-discovery**: New game modes are picked up automatically from `models/*_mode.py` — no registration needed, and applied to every dataset.
- **Generic routes**: `/check` delegates to `mode.handle_answer()` — no if-elif per mode.
- **i18n**: Flask-Babel with FR/EN catalogs, cookie-based locale switching.
- **Flexible scores**: Per-mode tracking with a generic `stat_updates` dict; stored per dataset.

### Adding a New Game Mode

Create `models/my_mode.py`:

```python
from flask_babel import lazy_gettext as _l
from .game_mode import GameMode

class MyMode(GameMode):
    @property
    def name(self) -> str:
        return 'my_mode'

    @property
    def description(self) -> str:
        return _l('Description of my mode')

    @property
    def template(self) -> str:
        return 'my_mode.html'

    def get_question_data(self, data_id, used_indices, current_question):
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected
        return {
            'game_over': False,
            'image_url': selected['photo'],
            'correct_name': self._make_full_name(selected),
            'name_choices': self._get_name_choices(selected),
            'current_question': current_question,
        }

    def update_score(self, user_id, **kwargs):
        if kwargs.get('correct_answer'):
            self.game_manager.score_manager.update_score(
                user_id, score_increment=1, stat_updates={'name': 1}
            )
```

Create `templates/my_mode.html` extending `base_game.html`. That's it -- auto-discovery handles registration.
