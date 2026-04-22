# Le Jeu Des Images

Company-agnostic team recognition game. 22 game modes. **Multi-dataset** runtime — users can register any number of datasets (CSV + photos + branding per company) via the `/setup` admin UI and switch between them at runtime, no restart needed. Zero YAML editing required.

## Critical Rules

1. **Never hardcode company data** -- names, emails, logos come from `config.yaml` only (or the `/setup` wizard)
2. **Always use canonical field names** -- `first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`, `birth_date`, `contract_start`, `manager_name`. Never reference CSV column names.
3. **All user-visible text must be i18n** -- `{{ _('...') }}` in templates, `_l('...')` in Python
4. **New templates must extend a base** -- `base_game.html`, `base_page.html`, or `base.html`
5. **config.yaml is gitignored** -- only `config.example.yaml` is committed. No personal data in repo.
6. **Use `Employee` class** -- `models/employee.py:Employee(dict)` provides `full_name`, `image_url`, `name`, `position`, `id` properties. Never manually enrich dicts.
7. **Resolve dataset per request** -- in routes, use `registry.current(request)` to get the active `Dataset`. Never cache a dataset across requests.

## Stack

Flask, Flask-Babel (FR/EN), Python 3.10+, pandas, TinyDB, Alpine.js, Docker

## Quick Reference

```bash
make test          # non-E2E tests (unit + integration + flow)
make test-e2e      # Playwright E2E tests (needs: uv run playwright install chromium)
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
app.py                     # Entry point — builds DatasetRegistry, registers blueprints
config.example.yaml        # Template config (config.yaml is gitignored)
Dockerfile / docker-compose.yml
DEPLOY.md                  # Deployment guide
CONTRIBUTING.md            # Open-source contributor guide
LICENSE                    # MIT

models/
  config.py                # AppConfig + DatasetConfig (+ CompanyConfig back-compat wrapper)
  dataset.py               # Dataset — bundles EmployeeData/ScoreManager/GameManager per dataset
  dataset_registry.py      # DatasetRegistry — runtime registry, cookie-based resolution
  employee.py              # Employee(dict) + EmployeeData (CSV load + CRUD + save)
  score.py                 # ScoreManager -- per-mode scores, best_score tracking
  game.py                  # GameManager -- data cache only (no mode logic)
  game_mode.py             # GameMode ABC + helpers + NormalMode + ReverseMode + Factory
  *_mode.py                # 20+ modes (auto-discovered, no registration needed)

routes/
  game_routes.py           # init_routes(registry) → Blueprint; per-request dataset resolution
  card_game_routes.py      # Card game API; same registry pattern
  admin_routes.py          # /setup CRUD: datasets + employees (ADMIN_PASSWORD env)

templates/
  base.html -> base_page.html -> page templates (mode_selection, about, scores, ...)
  base.html -> base_game.html -> game templates (Alpine.js powered)
  _switchers.html          # Header partial: language + dataset dropdowns
  setup_list.html          # Dataset management landing (list + actions)
  setup_wizard.html        # Add / edit dataset wizard (4 steps)
  employees_list.html      # Per-dataset employee list with search
  employee_edit.html       # Per-employee form + inline photo upload

static/game-alpine.js      # Alpine.js components (timer, answer checking, progress bar)
static/setup.css           # Shared styles for /setup* admin pages
data/<dataset_id>/         # Per-dataset storage — team.csv, photos/, scores.json (all gitignored)
translations/              # FR/EN catalogs
tests/                     # unit + integration + flow + E2E (Playwright)
tools/validate_data.py     # CSV + photo validation CLI

.claude/                   # Claude Code integration
  settings.json            # Permissions, pre-commit hooks
  agents/                  # game-mode-creator, i18n-updater, template-migrator, ...
  commands/                # add-game-mode, update-translations, check-release, ...
  memory/                  # Architecture decisions, known patterns/pitfalls
```

## Multi-Dataset Architecture

A **dataset** is a self-contained collection: company branding + employees CSV + photos + scores DB. The app can hold N datasets simultaneously; the active one per request is determined by the `dataset` cookie (falls back to the default configured in `config.yaml`). Each dataset has its own `data/<id>/` subtree.

```
  AppConfig (one)              DatasetRegistry (one)
  ├── contact_email             {
  └── default_dataset_id          "acme":     Dataset(DatasetConfig, EmployeeData, ScoreManager, GameManager, GameModeFactory),
  ├── datasets: {               "client_x": Dataset(...),
  │     "acme":     DatasetConfig,          ...
  │     "client_x": DatasetConfig,         }
  │     ...                    }
  │   }
```

**Resolution flow (per request)**:
1. `@app.before_request` — redirects to `/setup` if registry empty (first-run)
2. `inject_globals` + routes call `registry.current(request)` — reads `dataset` cookie, falls back to `registry.default_id`
3. Each `Dataset` holds its own `GameModeFactory` / `ScoreManager` — modes never share state across datasets

**Legacy config auto-migration**: if `config.yaml` uses the old single-dataset format (top-level `company` + `data`), `AppConfig` silently converts it to a single `default` dataset with `app.contact_email` extracted from `company.contact_email`.

**Managing datasets**: the `/setup` admin UI (password-gated via `ADMIN_PASSWORD` env) provides full CRUD on datasets and employees — all changes persist to `config.yaml` + filesystem and hot-reload the registry without restart.

## Adding a New Game Mode

Use the `game-mode-creator` agent or do it manually:

1. Create `models/my_mode.py` -- extend `GameMode`, use helpers `_pick_next_employee()`, `_get_name_choices()`, `_make_full_name()`. Wrap description in `_l()`.
2. Create `templates/my_mode.html` -- extend `base_game.html`. Use Alpine.js `x-data="singleAnswer('{{ correct }}')"` + `@click="check(value, $el)"`. Wrap text in `_()`.
3. Done. Auto-discovery handles registration across every dataset.

Reference: `models/pixelation_mode.py` (simple), `models/clue_mode.py` (complex).

## Adding a New Dataset

Via the UI (recommended): go to `/setup` → *Ajouter un dataset* → wizard. Identifier, CSV upload with column mapping, optional photos ZIP, save. Hot-reloaded into the registry; no restart needed.

Via YAML (advanced): append a dataset entry under `datasets:` in `config.yaml`, drop the CSV at `data/<id>/team.csv` and photos under `data/<id>/photos/`. Restart the app.

## Architecture (brief)

- **Auto-discovery**: `pkgutil.iter_modules` scans `models/*_mode.py` -- no imports in app.py. Each `Dataset` auto-registers every mode against its own `GameManager`.
- **Blueprint factories**: `init_routes(registry)` and `register_card_game_blueprint(app, registry)` build fresh blueprints inside the function so `create_app()` is re-entrant (for multi-app test scenarios).
- **Generic routes**: `/check` calls `mode.handle_answer(user_id, form, session)` -- no if-elif, no mode special-casing
- **Employee class**: `Employee(dict)` with computed properties (`full_name`, `image_url`, `name`, `position`, `id`). All modes return Employee objects, no manual enrichment.
- **Column mapping**: applied once in `EmployeeData.__init__()` via `config.reverse_mapping()`. Writing back via `EmployeeData.save()` restores the original CSV column names.
- **GameManager**: pure data cache (`store_game_data`/`get_game_data`). No mode-specific logic.
- **Scores**: per-dataset TinyDB at `data/<id>/scores.json`. Switching datasets never mixes scores.
- **Frontend**: Alpine.js components (`gameTimer`, `singleAnswer`, `imageAnswer`, `normalMode`, `progressBar`). No vanilla JS globals. State in `Alpine.store('game')`.
- **i18n**: `_()` in templates, `_l()` for class-level strings, cookie-based locale (`/lang/fr`, `/lang/en`). JS reads i18n from `data-label` attributes.

## Route Map

```
GET  /                                       -> mode selection (for active dataset)
GET  /mode/<name>                            -> initialize game -> /question
GET  /question                               -> render mode template
POST /check                                  -> mode.handle_answer() -> /question or /result
GET  /result                                 -> result page
GET  /photos/<file>                          -> serve from active dataset's images_dir
GET  /lang/<code>                            -> set locale cookie
GET  /dataset/<id>                           -> set active dataset cookie + clear session

GET  /setup                                  -> datasets landing (list + actions)
GET  /setup/new                              -> wizard: add dataset
GET  /setup/<id>/edit                        -> wizard: edit dataset config
POST /setup/save                             -> persist dataset + hot-reload registry
POST /setup/<id>/delete                      -> remove dataset (disk + registry + config.yaml)
POST /setup/upload-csv                       -> validate CSV, preview
POST /setup/<id>/upload-photos               -> extract ZIP to dataset's photos dir
POST /setup/<id>/replace-csv                 -> swap CSV, reload Dataset

GET  /setup/<id>/employees                   -> list employees (searchable)
GET  /setup/<id>/employees/new               -> new-employee form
POST /setup/<id>/employees                   -> create employee + persist CSV
GET  /setup/<id>/employees/<idx>/edit        -> edit form
POST /setup/<id>/employees/<idx>             -> update + persist
POST /setup/<id>/employees/<idx>/delete      -> delete + persist
POST /setup/<id>/employees/<idx>/photo       -> upload individual photo
```

All `/setup*` routes are gated behind `ADMIN_PASSWORD` if the env var is set.

## Conventions

- **Commits**: `type(scope): description` -- feat, fix, refactor, chore, docs, test
- **Python**: PEP 8, ruff enforced, pyright basic mode (0 errors)
- **Tests**: `tests/`, pytest, fixtures in `conftest.py`. E2E tests marked `@pytest.mark.e2e`
- **JS**: Alpine.js components in `static/game-alpine.js`. No inline `game_scripts` blocks (except 5 modes with custom effects).
- **No company data in repo**: `config.yaml`, `data/`, `static/images/` are all gitignored. Each dataset lives under `data/<id>/`.
- **Dataset IDs**: lowercase alphanumeric + `_-`, 1-32 chars (enforced in `/setup/save`).
