# Le Jeu Des Images

A company-agnostic team recognition game — identify your colleagues from photos across 21 game modes. Register **multiple datasets** (one per company) from the browser and switch between them at runtime; no YAML editing required.

![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen)
![Flask](https://img.shields.io/badge/Flask-2.3%2B-orange)
![i18n](https://img.shields.io/badge/i18n-FR%20%7C%20EN-blue)
![Docker](https://img.shields.io/badge/Docker-ready-blue)

## TL;DR

```bash
cp .env.example .env        # fill SECRET_KEY + ADMIN_PASSWORD
make demo-dataset           # seed data/demo/ (10 playable placeholder employees)
make run                    # -> http://127.0.0.1:5000
```

Visit `/setup` to manage datasets (password-gated by `ADMIN_PASSWORD`). The app boots without any `config.yaml` — on first launch you're redirected to the wizard.

## Quick Start by environment

Pick the setup that matches where you run your shell. The project is developed and tested on Linux / WSL; the PowerShell notes only document the gotchas when you toggle between the two.

### Option A — Linux / macOS / **WSL** (recommended)

```bash
# 1. Install dependencies
uv sync --extra dev

# 2. Configure secrets
cp .env.example .env
# Edit .env and set:
#   SECRET_KEY=...     (uv run python -c "import secrets; print(secrets.token_hex(32))")
#   ADMIN_PASSWORD=... (any value you like; leave empty to disable auth in dev)

# 3. Install the bundled demo dataset (copies demo/ -> data/demo/)
make demo-dataset

# 4. Run the app
make run
# -> http://127.0.0.1:5000  (game)
# -> http://127.0.0.1:5000/setup  (admin, ADMIN_PASSWORD required)
```

### Option B — Docker (Linux / macOS / Windows)

```bash
cp .env.example .env        # fill secrets
make demo-dataset           # optional — seed data/demo/ so the first visit works straight away
docker compose up
# -> http://localhost:5000
```

The compose file runs the container as `${UID}:${GID}` so any file written to the bind-mounted `./data` and `./uploads` stays owned by your host user. On Linux, export `UID` / `GID` if they aren't already in your shell:

```bash
export UID GID=$(id -g)
docker compose up
```

### Option C — Windows **PowerShell** (native, no WSL)

Works, but watch the two gotchas below.

```powershell
# 1. Create a Windows-native venv via uv
uv sync --extra dev

# 2. Configure secrets
Copy-Item .env.example .env
notepad .env           # set SECRET_KEY and ADMIN_PASSWORD

# 3. Seed the demo dataset (PowerShell, no make)
New-Item -ItemType Directory -Force data\demo\photos | Out-Null
Copy-Item demo\team.csv data\demo\team.csv
Copy-Item demo\photos\*.png data\demo\photos\

# 4. Run the app
uv run python app.py
# -> http://127.0.0.1:5000
```

**Gotcha 1 — don't mix WSL and Windows in the same `.venv`.**
`uv sync` from WSL creates a Linux-layout venv with a `lib64` symlink that Windows can't delete. If you switch shells you'll see:

```
error: failed to remove file `.venv\lib64`: Accès refusé. (os error 5)
```

Fix:

```powershell
# from PowerShell
Remove-Item -Recurse -Force .venv
# if "Access denied", fall back to cmd:
cmd /c "rmdir /s /q .venv"
uv sync --extra dev
```

Rule of thumb: pick one shell per working tree and stick with it. If you need both, clone the repo twice.

**Gotcha 2 — `make` is not installed by default on Windows.** Use the `uv run` / `docker compose` / `Copy-Item` commands shown above; the `make` targets are just thin shortcuts.

### Mixing Docker and a local run

Don't start both against the same port. Either `docker compose down` before `make run`, or change `FLASK_PORT` in `.env`. When Docker is already up, you reach the app at the same URL — just copy files into `./data/demo/` (the volume is mounted) and `docker compose restart` to pick them up.

## Admin Access (`/setup`)

The `/setup` wizard is **protected by `ADMIN_PASSWORD`** — an env var you set in `.env`.

How authentication works:

1. **Set the password** in `.env`:
   ```bash
   ADMIN_PASSWORD=your-secret-password
   ```
   Then restart the app (`docker compose restart` or relaunch `uv run python app.py`).

2. **Visit `/setup`** — if you're not logged in you're redirected to `/setup/login`, a standard HTML form. Enter the password and you're signed in for the session (signed cookie).

   Scripted callers (JSON clients, automation) can still pass `?password=...` in the query string on any `/setup*` URL to skip the form.

3. **Subsequent visits** — the cookie does the job until you log out or the session expires.

**Logout**: POST to `/setup/logout` (link from the admin UI), clear browser cookies, or change `SECRET_KEY` (invalidates all sessions).

**Security notes**:
- `ADMIN_PASSWORD` unset → `/setup` is open to everyone (dev mode only — never ship to production without a password).
- **First-run bypass**: when no dataset is configured yet, `/setup` is reachable even with `ADMIN_PASSWORD` set, so the very first dataset can be bootstrapped. Once a dataset exists, the password is required again.
- `SECRET_KEY` must be a long random string; regenerate with `python -c "import secrets; print(secrets.token_hex(32))"`.
- Do **not** commit your real `.env` — it's already gitignored.

## The bundled demo dataset

The repo ships a ready-to-play dataset under `demo/`:

```
demo/
  team.csv              # 10 fictional DemoTech employees
  photos/*.png          # 10 distinct initial-based avatars (generated)
```

`make demo-dataset` (or the PowerShell `Copy-Item` equivalent above) copies this to `data/demo/` — the live location the app reads from — so the very first `make run` has something to show.

Regenerate the avatars (e.g. after editing `demo/team.csv`) with:

```bash
uv run python tools/generate_demo_avatars.py
```

The avatars are intentionally stylised placeholders (coloured gradient + face + initials) so visual modes like pixelation, mirror, and scrambled_face still work and each person stays visually distinct.

## Setup for a New Company

Each company lives as an independent **dataset**: CSV + photos + branding, all configurable through `/setup`.

1. Go to `/setup` → *Ajouter un dataset* (*Add a dataset*).
2. Wizard:
   - Step 1: pick a dataset id + company branding (name, logo, tagline).
   - Step 2: upload your CSV, map columns to the game's canonical fields (`first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`, + optional `birth_date`, `contract_start`, `manager_name`).
   - Step 3: upload photos (ZIP) — optional at create time; can be done later.
   - Step 4: review + save.
3. Dataset is hot-registered — no restart. Switch via the header dropdown.
4. Per-employee edits (rename, replace photo, delete) available from *Employés* on the dataset card.

See [docs/data-format.md](docs/data-format.md) for the CSV specification.

Validate your setup:

```bash
uv run python tools/validate_data.py
```

## Game Modes

### Classic
- **Normal** — Identify company, team, name, and position from a photo
- **Reverse** — Identify the person from a name
- **Pixelation** — Progressively clearer image
- **Timed** — Max identifications in 2 minutes
- **Team** — Identify all members of a team
- **Quiz** — Answer questions about colleagues

### Advanced
- **Clue** — Progressive hints
- **Memory** — Card matching game
- **Speed** — Max identifications in a time limit
- **Team Guess** — Guess which team someone belongs to
- **Missing Person** — Find the missing person
- **Position Match** — Match people to positions
- **Progressive Hint** — Hints gradually revealed
- **Manager** — Identify someone's manager
- **Seniority** — Guess years of seniority
- **Age** — Guess someone's age

### Creative
- **Scrambled Face** — Facial features mixed from multiple people
- **Emoji Challenge** — Identify from emoji clues
- **Silhouette** — Black silhouettes only
- **Mirror** — Horizontally flipped images

### Special
- **ARR** — Hidden arcade racing game (Konami code: ↑ ↑ ↓ ↓ ← → ← → B A)

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run non-e2e tests (326 tests)
make test

# Run Playwright E2E tests (requires `uv run playwright install chromium` once)
make test-e2e

# Lint
make lint

# Type check (pyright, basic mode)
make typecheck

# Format
make format

# Validate employee data
make validate-data

# i18n: extract new strings after code changes
make babel-extract
make babel-compile
```

CI / quality gates currently green: 326 non-e2e tests, 0 ruff errors, 0 pyright errors.

## Architecture

```
app.py                     # Entry point — builds DatasetRegistry, registers blueprints
config.yaml                # app-level settings + datasets registry (gitignored)
config.example.yaml        # template (committed)
demo/                      # bundled sample dataset (CSV + avatars), committed
tools/
  generate_demo_avatars.py # regenerate demo/photos/*.png from demo/team.csv
  validate_data.py         # CSV + photo validation CLI
models/
  config.py                # AppConfig + DatasetConfig (+ CompanyConfig back-compat)
  dataset.py               # Dataset — bundles EmployeeData/ScoreManager/GameManager per id
  dataset_registry.py      # Runtime registry, cookie-based resolution
  employee.py              # Employee(dict) + EmployeeData (CSV load + CRUD + save)
  score.py                 # ScoreManager (per-dataset TinyDB)
  game.py                  # GameManager (core orchestration)
  game_mode.py             # GameMode ABC + helpers + Factory
  *_mode.py                # 21 game modes (auto-discovered per dataset)
routes/
  game_routes.py           # Per-request dataset resolution
  admin_routes.py          # /setup datasets + employees CRUD (+ login form)
templates/
  base.html → base_page.html / base_game.html
  _switchers.html          # Header partial (language + dataset dropdown)
  setup_list.html          # Datasets landing
  setup_login.html         # Admin login form
  setup_wizard.html        # Add / edit dataset wizard
  employees_list.html      # Per-dataset employees
  employee_edit.html       # Per-employee form
data/<dataset_id>/         # Per-dataset CSV + photos + scores (all gitignored)
translations/              # Flask-Babel FR/EN
tests/                     # pytest — unit, integration, E2E (Playwright)
```

### Key Design Decisions

- **Multi-dataset runtime**: N datasets loaded simultaneously, switched per request via the `dataset` cookie. Scores, branding, data all isolated. No restart to add/remove datasets.
- **Legacy config auto-migration**: old single-dataset `config.yaml` is silently promoted to a single dataset named `default`.
- **Company-agnostic**: all company data lives in `config.yaml` + `data/` (gitignored). Zero hardcoded references in code. Only the bundled `demo/` fixture is committed.
- **Auto-discovery**: new game modes are picked up automatically from `models/*_mode.py` — no registration needed, and applied to every dataset.
- **Generic routes**: `/check` delegates to `mode.handle_answer()` — no if-elif per mode.
- **i18n**: Flask-Babel with FR/EN catalogs, cookie-based locale switching, `display_name` on every mode for translated UI labels.
- **Flexible scores**: per-mode tracking with a generic `stat_updates` dict; stored per dataset under `data/<id>/scores.json`.

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
    def display_name(self) -> str:
        return _l('My Mode')

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

Create `templates/my_mode.html` extending `base_game.html`. That's it — auto-discovery handles registration.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `PermissionError: data/<id>/scores.json` on `make run` / `pytest` | The dir was created by an earlier `docker compose up` without `user:` mapping and is root-owned | `sudo rm -rf data/<id>` then re-run `make demo-dataset`; compose now uses `${UID}:${GID}` so it won't happen again |
| `/setup` returns `{"error":"Unauthorized"}` | Non-browser client and `ADMIN_PASSWORD` is set | Either log in via `/setup/login` in a browser, or append `?password=...` to the URL |
| `uv sync` fails with `Accès refusé` on `.venv\lib64` | Existing Linux-layout venv inherited from WSL | `rm -rf .venv` (WSL) or `cmd /c "rmdir /s /q .venv"` (PowerShell), then `uv sync --extra dev` |
| Home page shows `Card_game` with an underscore | Stale browser cache / `.mo` not rebuilt | `make babel-compile` then hard refresh (Ctrl+F5) |
| English tagline still appears in French | Dataset tagline comes from `config.yaml`, not i18n | This is branded content — edit it in `/setup` → *Modifier* |

## License

MIT — see `LICENSE`.
