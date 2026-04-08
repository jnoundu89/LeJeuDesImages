# Le Jeu Des Images

Company-agnostic team recognition game -- identify colleagues from photos across 19+ game modes. Configurable for any company via `config.yaml` or the `/setup` admin wizard.

## Stack

- **Backend**: Flask, Flask-Babel (i18n), Python 3.10+, pandas, TinyDB, python-dotenv, pyyaml
- **Frontend**: Vanilla JS (`GameEngine` IIFE), CSS3 (animations, glassmorphism, responsive)
- **Data**: CSV (configurable path in `data/`), TinyDB (`scores_db.json`)
- **Config**: `config.yaml` (company branding + CSV column mapping) -- gitignored, use `config.example.yaml` as template
- **Deploy**: Docker (`docker compose up`) or local (`uv run python app.py`)
- **i18n**: Flask-Babel, FR/EN catalogs in `translations/`

## Project Structure

```
app.py                     # Flask entry point, auto-discovery, Babel, context processor, /photos route
config.example.yaml        # Reference config (config.yaml is gitignored)
Dockerfile / docker-compose.yml
models/
  config.py                # CompanyConfig -- loads/saves config.yaml
  employee.py              # EmployeeData -- CSV with column normalization at load time
  score.py                 # ScoreManager -- TinyDB, per-mode scores, flexible stats dict
  game.py                  # GameManager -- core game orchestration, cache
  game_mode.py             # GameMode ABC + helpers + NormalMode + ReverseMode + Factory
  *_mode.py                # 18+ concrete game modes (auto-discovered via pkgutil)
routes/
  game_routes.py           # Game routes (generic /check via mode.handle_answer)
  card_game_routes.py      # Card game API blueprint
  admin_routes.py          # /setup wizard (CSV upload, column mapping, photo upload)
templates/
  base.html                # Root template (blocks: lang, title, meta, extra_css, body, scripts)
  base_page.html           # Pages: header, footer, music player, particles, lang switcher
  base_game.html           # Game modes: 3-column layout, stats, timer, form, GameEngine
  setup.html               # Admin setup wizard (4 steps, vanilla JS)
  *.html                   # 30 child templates using {% extends %}
static/
  game-engine.js           # GameEngine IIFE (checkAnswer, timer, confetti, progress)
  scripts.js               # Thin wrappers + Konami code easter egg
  styles.css / homepage.css / animations.css / ...
translations/              # Flask-Babel FR/EN catalogs (227 strings)
tests/                     # 65 pytest tests (88% coverage on core modules)
  conftest.py              # Shared fixtures (test_config, test_employee_data, test_score_manager, app)
  fixtures/                # Test CSV + YAML configs
tools/
  validate_data.py         # CLI: validate CSV + photos against config
docs/
  data-format.md           # CSV format documentation
  DEPLOY.md -> ../DEPLOY.md
data/                      # Gitignored -- company CSV + photos go here
```

## Canonical Employee Fields

All code uses these canonical names. CSV columns are mapped via `config.yaml` `data.column_mapping` at load time in `EmployeeData.__init__()`.

| Canonical | Description | Required | Used by |
|-----------|-------------|----------|---------|
| `first_name` | First name | Yes | All modes |
| `last_name` | Last name | Yes | All modes |
| `photo` | Path to photo | Yes | All modes |
| `team` | Department / team | Yes | team, team_guess, silhouette, clue modes |
| `job_title` | Job title | Yes | normal, quiz, silhouette, clue modes |
| `company` | Legal entity | Yes | normal mode |
| `sex` | Gender (`man`/`woman`) | Yes | Name choice filtering in all modes |
| `birth_date` | Birth date (ISO) | No | age mode |
| `contract_start` | Contract start date | No | seniority mode |
| `manager_name` | Manager full name | No | manager, clue modes |

## Key Architecture Patterns

### Auto-discovery
`app.py` uses `pkgutil.iter_modules` to scan `models/*_mode.py` for `GameMode` subclasses. No manual registration needed. Adding a mode = create `models/my_mode.py` + `templates/my_mode.html`.

### GameMode base class (`models/game_mode.py`)
- `initialize()` -- default implementation (shuffle employees, store in cache)
- `get_question_data()` -- abstract, each mode implements
- `update_score()` -- abstract, each mode implements
- `handle_answer(user_id, form_data, session_data)` -- default reads `correct_answer` from form. Override for modes with different form structures (NormalMode, ARRMode, MemoryMode)
- `_pick_next_employee(data_id, used_indices, current_question)` -- shared helper
- `_get_name_choices(selected_employee, count=4)` -- shared helper, filters by sex
- `_make_full_name(employee)` -- returns `"FirstName LastName"`

### Template inheritance
```
base.html
  +-- base_page.html  (mode_selection, about, how_to_play, scores, setup)
  +-- base_game.html  (all 24 game mode templates)
  +-- result.html, arr_mode.html (extend base.html directly)
```

### Route flow
```
GET /                -> mode_selection.html (carousel of modes)
GET /mode/<name>     -> mode.initialize() -> session setup -> redirect to /question
GET /question        -> mode.get_question_data() -> render mode.template
POST /check          -> mode.handle_answer() -> redirect to /question (or /result)
GET /result          -> result.html
GET /setup           -> setup wizard (admin)
GET /photos/<file>   -> serve from config.images_dir
GET /lang/<code>     -> set locale cookie
```

### Score system (`models/score.py`)
- `initialize_user(user_id, mode, player_name)` -- creates TinyDB record
- `update_score(user_id, score_increment, stat_updates={'name': 1})` -- flexible stats dict
- `get_top_scores(mode)` -- filter by mode or return all
- Backwards-compatible with legacy flat `stats_company/team/name/position` fields

### i18n
- Templates: `{{ _('French text') }}`
- Python mode descriptions: `from flask_babel import lazy_gettext as _l`
- Cookie-based locale: `/lang/fr`, `/lang/en`
- Extraction: `make babel-extract`, compilation: `make babel-compile`

## Common Operations

```bash
# Run locally
uv run python app.py

# Run tests
make test

# Lint + format
make lint && make format

# Validate employee data
make validate-data

# i18n workflow
make babel-extract    # after changing template text
# edit translations/en/LC_MESSAGES/messages.po
make babel-compile

# Docker
docker compose up
```

## Adding a New Game Mode

1. Create `models/my_mode.py`:
```python
from flask_babel import lazy_gettext as _l
from .game_mode import GameMode

class MyMode(GameMode):
    @property
    def name(self): return 'my_mode'

    @property
    def description(self): return _l('My mode description')

    @property
    def template(self): return 'my_mode.html'

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
            self.game_manager.score_manager.update_score(user_id, 1, stat_updates={'name': 1})
```

2. Create `templates/my_mode.html` extending `base_game.html`
3. Done -- auto-discovery handles registration

## Conventions

- **Commit messages**: `type(scope): description` (feat, fix, refactor, chore, docs, test)
- **Python**: PEP 8, ruff enforced, single quotes preferred
- **i18n**: ALL user-visible text must use `_()` in templates, `_l()` in Python
- **Config**: Company-specific data goes in `config.yaml` + `data/`, never hardcoded
- **Tests**: `tests/` directory, pytest, fixtures in `tests/conftest.py`
