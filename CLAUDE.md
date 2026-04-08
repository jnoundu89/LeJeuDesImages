# Le Jeu Des Images

Company-agnostic team recognition game. 22 game modes, configurable for any company via `config.yaml` or `/setup` wizard.

## Critical Rules

1. **Never hardcode company data** -- names, emails, logos come from `config.yaml` only
2. **Always use canonical field names** -- `first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`, `birth_date`, `contract_start`, `manager_name`. Never reference CSV column names.
3. **All user-visible text must be i18n** -- `{{ _('...') }}` in templates, `_l('...')` in Python
4. **New templates must extend a base** -- `base_game.html`, `base_page.html`, or `base.html`
5. **config.yaml is gitignored** -- only `config.example.yaml` is committed. No personal data in repo.
6. **Use `Employee` class** -- `models/employee.py:Employee(dict)` provides `full_name`, `image_url`, `name`, `position`, `id` properties. Never manually enrich dicts.

## Stack

Flask, Flask-Babel (FR/EN), Python 3.10+, pandas, TinyDB, Alpine.js, Docker

## Quick Reference

```bash
make test          # 253 tests (excludes E2E)
make test-e2e      # 7 Playwright E2E tests (needs: uv run playwright install chromium)
make typecheck     # pyright type checking (models/ + routes/)
make lint          # ruff
make format        # ruff format
make validate-data # check CSV + photos
make babel-extract # extract i18n strings after code changes
make babel-compile # compile .po -> .mo
make run           # start Flask app
docker compose up  # start via Docker
```

## Project Structure

```
app.py                     # Entry point (accepts config_path param for testing)
config.example.yaml        # Template config (config.yaml is gitignored)
Dockerfile / docker-compose.yml
DEPLOY.md                  # Deployment guide (local, Docker, Railway, Render)
CONTRIBUTING.md            # Open-source contributor guide
LICENSE                    # MIT

models/
  config.py                # CompanyConfig -- load/save config.yaml
  employee.py              # Employee(dict) class + EmployeeData (CSV loader)
  score.py                 # ScoreManager -- per-mode scores, best_score tracking
  game.py                  # GameManager -- data cache only (no mode logic)
  game_mode.py             # GameMode ABC + helpers + NormalMode + ReverseMode + Factory
  *_mode.py                # 20+ modes (auto-discovered, no registration needed)

routes/
  game_routes.py           # Generic /check via mode.handle_answer(), no mode special-casing
  card_game_routes.py      # Card game API
  admin_routes.py          # /setup wizard (password-protected via ADMIN_PASSWORD env)

templates/
  base.html -> base_page.html -> page templates (mode_selection, about, scores, ...)
  base.html -> base_game.html -> game templates (Alpine.js powered)
  setup.html               # Admin wizard (extends base.html)

static/game-alpine.js      # Alpine.js components (timer, answer checking, progress bar)
translations/              # FR/EN catalogs
tests/                     # 253 tests (unit + integration + flow, 7 E2E Playwright)
tools/validate_data.py     # CSV + photo validation CLI

.claude/                   # Claude Code integration
  settings.json            # Permissions, pre-commit hooks
  agents/                  # game-mode-creator, i18n-updater, template-migrator,
                           # release-preparer, code-reviewer, ui-tester
  commands/                # add-game-mode, update-translations, check-release,
                           # test-ui, add-company-data (slash commands)
  memory/                  # Architecture decisions, known patterns/pitfalls
```

## Adding a New Game Mode

Use the `game-mode-creator` agent or do it manually:

1. Create `models/my_mode.py` -- extend `GameMode`, use helpers `_pick_next_employee()`, `_get_name_choices()`, `_make_full_name()`. Wrap description in `_l()`.
2. Create `templates/my_mode.html` -- extend `base_game.html`. Use Alpine.js `x-data="singleAnswer('{{ correct }}')"` + `@click="check(value, $el)"`. Wrap text in `_()`.
3. Done. Auto-discovery handles registration.

Reference: `models/pixelation_mode.py` (simple), `models/clue_mode.py` (complex).

## Architecture (brief)

- **Auto-discovery**: `pkgutil.iter_modules` scans `models/*_mode.py` -- no imports in app.py
- **Generic routes**: `/check` calls `mode.handle_answer(user_id, form, session)` -- no if-elif, no mode special-casing
- **Employee class**: `Employee(dict)` with computed properties (`full_name`, `image_url`, `name`, `position`, `id`). All modes return Employee objects, no manual enrichment.
- **Column mapping**: applied once in `EmployeeData.__init__()` via `config.reverse_mapping()`
- **GameManager**: pure data cache (`store_game_data`/`get_game_data`). No mode-specific logic.
- **Scores**: `update_score(user_id, increment, stat_updates={'name': 1})` -- flexible dict, per-mode. `best_score` tracked automatically.
- **Frontend**: Alpine.js components (`gameTimer`, `singleAnswer`, `imageAnswer`, `normalMode`, `progressBar`). No vanilla JS globals. State in `Alpine.store('game')`.
- **i18n**: `_()` in templates, `_l()` for class-level strings, cookie-based locale (`/lang/fr`, `/lang/en`). JS reads i18n from `data-label` attributes.

## Route Map

```
GET  /              -> mode selection
GET  /mode/<name>   -> initialize game -> /question
GET  /question      -> render mode template
POST /check         -> mode.handle_answer() -> /question or /result
GET  /result        -> result page
GET  /setup         -> admin wizard (ADMIN_PASSWORD env)
GET  /photos/<file> -> serve from config.images_dir
GET  /lang/<code>   -> set locale cookie
```

## Conventions

- **Commits**: `type(scope): description` -- feat, fix, refactor, chore, docs, test
- **Python**: PEP 8, ruff enforced, pyright basic mode (0 errors)
- **Tests**: `tests/`, pytest, fixtures in `conftest.py`. E2E tests marked `@pytest.mark.e2e`
- **JS**: Alpine.js components in `static/game-alpine.js`. No inline `game_scripts` blocks (except 5 modes with custom effects).
- **No company data in repo**: `config.yaml`, `data/`, `static/images/` are all gitignored
