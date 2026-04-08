# Le Jeu Des Images

Company-agnostic team recognition game. 19+ game modes, configurable for any company via `config.yaml` or `/setup` wizard.

## Critical Rules

1. **Never hardcode company data** -- names, emails, logos come from `config.yaml` only
2. **Always use canonical field names** -- `first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`, `birth_date`, `contract_start`, `manager_name`. Never reference CSV column names.
3. **All user-visible text must be i18n** -- `{{ _('...') }}` in templates, `_l('...')` in Python
4. **New templates must extend a base** -- `base_game.html`, `base_page.html`, or `base.html`
5. **config.yaml is gitignored** -- only `config.example.yaml` is committed. No personal data in repo.

## Stack

Flask, Flask-Babel (FR/EN), Python 3.10+, pandas, TinyDB, vanilla JS (`GameEngine` IIFE), Docker

## Quick Reference

```bash
make test          # 65 unit tests (excludes E2E)
make test-e2e      # 7 Playwright E2E tests (needs: uv run playwright install chromium)
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
  employee.py              # EmployeeData -- column normalization at load time
  score.py                 # ScoreManager -- per-mode scores, flexible stat_updates dict
  game.py                  # GameManager -- orchestration, cache
  game_mode.py             # GameMode ABC + helpers + NormalMode + ReverseMode + Factory
  *_mode.py                # 18+ modes (auto-discovered, no registration needed)

routes/
  game_routes.py           # Generic /check via mode.handle_answer()
  card_game_routes.py      # Card game API
  admin_routes.py          # /setup wizard (password-protected via ADMIN_PASSWORD env)

templates/
  base.html -> base_page.html -> page templates (mode_selection, about, scores, ...)
  base.html -> base_game.html -> game templates (pixelation, timed, clue, ...)
  setup.html               # Admin wizard (extends base.html)

static/game-engine.js      # GameEngine IIFE (single source for checkAnswer, timer, confetti)
translations/              # FR/EN catalogs (227 strings)
tests/                     # 72 tests (65 unit + 7 E2E Playwright)
tools/validate_data.py     # CSV + photo validation CLI

.claude/                   # Claude Code integration
  settings.json            # Permissions, pre-commit hooks, Playwright MCP
  agents/                  # game-mode-creator, i18n-updater, template-migrator,
                           # release-preparer, code-reviewer, ui-tester
  commands/                # add-game-mode, update-translations, check-release,
                           # test-ui, add-company-data (slash commands)
  memory/                  # Architecture decisions, known patterns/pitfalls
```

## Adding a New Game Mode

Use the `game-mode-creator` agent or do it manually:

1. Create `models/my_mode.py` -- extend `GameMode`, use helpers `_pick_next_employee()`, `_get_name_choices()`, `_make_full_name()`. Wrap description in `_l()`.
2. Create `templates/my_mode.html` -- extend `base_game.html`. Wrap text in `_()`.
3. Done. Auto-discovery handles registration.

Reference: `models/pixelation_mode.py` (simple), `models/clue_mode.py` (complex).

## Architecture (brief)

- **Auto-discovery**: `pkgutil.iter_modules` scans `models/*_mode.py` -- no imports in app.py
- **Generic routes**: `/check` calls `mode.handle_answer(user_id, form, session)` -- no if-elif
- **Column mapping**: applied once in `EmployeeData.__init__()` via `config.reverse_mapping()`
- **Scores**: `update_score(user_id, increment, stat_updates={'name': 1})` -- flexible dict, per-mode
- **i18n**: `_()` in templates, `_l()` for class-level strings, cookie-based locale (`/lang/fr`, `/lang/en`)

For deeper architecture docs, see `.claude/memory/architecture-decisions.md`.
For known pitfalls, see `.claude/memory/known-patterns.md`.

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
- **Python**: PEP 8, ruff enforced, single quotes
- **Tests**: `tests/`, pytest, fixtures in `conftest.py`. E2E tests marked `@pytest.mark.e2e`
- **No company data in repo**: `config.yaml`, `data/`, `static/images/` are all gitignored
