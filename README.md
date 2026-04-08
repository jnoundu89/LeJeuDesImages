# Le Jeu Des Images

A company-agnostic team recognition game -- identify your colleagues from photos across 19+ game modes. Works for any company via a simple YAML config or the built-in setup wizard.

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
# Install dependencies
uv sync

# Configure
cp .env.example .env        # Edit SECRET_KEY, ADMIN_PASSWORD
cp config.example.yaml config.yaml  # Edit company branding + column mapping

# Place your data
# - CSV file in data/team.csv
# - Photos in data/photos/

# Run
uv run python app.py
# -> http://127.0.0.1:5000
```

### Option C: Setup Wizard

1. Start the app with default config
2. Go to `/setup`
3. Upload your CSV, map columns, upload photos, save

## Setup for a New Company

The game needs:
1. **A CSV file** with employee data (name, team, job title, company, photo path, gender)
2. **Employee photos** (JPG/PNG, any naming convention)
3. **A `config.yaml`** mapping your CSV columns to the game's canonical fields

See [docs/data-format.md](docs/data-format.md) for the full CSV specification.

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
app.py                     # Entry point, auto-discovery, Flask-Babel, context processor
config.yaml                # Company branding + CSV column mapping
models/
  config.py                # CompanyConfig (load/save YAML)
  employee.py              # EmployeeData (CSV with column normalization)
  score.py                 # ScoreManager (TinyDB, per-mode, flexible stats)
  game.py                  # GameManager (core orchestration)
  game_mode.py             # GameMode ABC + helpers + Factory
  *_mode.py                # 18+ game modes (auto-discovered)
routes/
  game_routes.py           # Game routes (generic /check via mode.handle_answer)
  card_game_routes.py      # Card game API
  admin_routes.py          # /setup wizard
templates/
  base.html                # Root template
  base_page.html           # Pages (header, footer, music player)
  base_game.html           # Game modes (3-column layout, stats, timer)
  setup.html               # Admin setup wizard
  *.html                   # 30 templates using {% extends %}
static/
  game-engine.js           # GameEngine IIFE (answer checking, timer, confetti)
  scripts.js               # Thin wrappers
translations/              # Flask-Babel FR/EN (227 strings)
tests/                     # 65 pytest tests
tools/validate_data.py     # CSV + photo validation CLI
docs/data-format.md        # CSV format documentation
```

### Key Design Decisions

- **Company-agnostic**: All company data lives in `config.yaml` + `data/` (gitignored). Zero hardcoded references in code.
- **Auto-discovery**: New game modes are picked up automatically from `models/*_mode.py` -- no registration needed.
- **Template inheritance**: 3 base templates, 30 child templates using `{% extends %}`.
- **Generic routes**: `/check` delegates to `mode.handle_answer()` -- no if-elif per mode.
- **i18n**: Flask-Babel with FR/EN catalogs, cookie-based locale switching.
- **Flexible scores**: Per-mode tracking with a generic `stat_updates` dict.

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
