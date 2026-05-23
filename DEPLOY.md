# Deployment Guide

The app boots without any `config.yaml`. On first launch with an empty or missing config, every route redirects to `/setup` so you can create your first dataset from the browser — zero YAML editing required.

## Prerequisites

- Python 3.10+ (or Docker)
- [`uv`](https://docs.astral.sh/uv/) for local runs (auto-installs a venv).
- Per dataset: a CSV of employees + their photos. Columns are flexible; you map them to the canonical fields (`first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`, and optionally `birth_date`, `contract_start`, `manager_name`) from the wizard.

## Option 1: Local (Linux / macOS / WSL)

```bash
# 1. Clone and install
git clone https://github.com/jnoundu89/LeJeuDesImages.git
cd LeJeuDesImages
uv sync --extra dev

# 2. Minimal env
cp .env.example .env
# In .env set at least:
#   SECRET_KEY=<random-string>   (uv run python -c "import secrets; print(secrets.token_hex(32))")
#   ADMIN_PASSWORD=<pick-one>    (required to access /setup)

# 3a. Bundled demo dataset (fastest way to see the game running)
make demo-dataset                # copies demo/ -> data/demo/
# Then edit config.yaml to point at data/demo/ — see `config.example.yaml`
# for the exact block, or copy config.yaml from config.example.yaml first
# and uncomment the `demo:` entry.

# 3b. OR skip demo and create your own dataset via the wizard on first run:
# (leave config.yaml missing, the app will redirect you to /setup)

# 4. Run
uv run python app.py            # or: make run
# -> http://127.0.0.1:5000       game
# -> http://127.0.0.1:5000/setup admin (redirects to /setup/login if ADMIN_PASSWORD is set)
```

To add more datasets, go to `/setup` → *Ajouter un dataset*. Switch between them via the dataset dropdown in the header.

### Windows (native PowerShell)

Everything above works; the only differences are:

- `cp` → `Copy-Item`, `mkdir -p` → `New-Item -ItemType Directory -Force`
- `make demo-dataset` isn't available by default — run the three commands it wraps manually:
  ```powershell
  New-Item -ItemType Directory -Force data\demo\photos | Out-Null
  Copy-Item demo\team.csv data\demo\team.csv
  Copy-Item demo\photos\*.png data\demo\photos\
  ```
- If you previously used `uv sync` from WSL in the same checkout, delete the Linux-layout `.venv` first (Windows can't remove the `lib64` symlink): `cmd /c "rmdir /s /q .venv"`.

## Option 2: Docker

```bash
git clone https://github.com/jnoundu89/LeJeuDesImages.git
cd LeJeuDesImages
cp .env.example .env                # fill SECRET_KEY + ADMIN_PASSWORD
make demo-dataset                   # optional — seed data/demo/ so the first visit works

export UID GID=$(id -g)             # Linux: ensure bind-mounted files stay yours
docker compose up
# -> http://localhost:5000
```

The compose file runs the container as `${UID}:${GID}` so everything written to the bind-mounted `./data`, `./uploads`, and `./config.yaml` stays owned by your host user (no more `sudo chown` after every run).

Persisted bind mounts:
- `./data` — per-dataset CSV + photos + `scores.json`
- `./uploads` — temp directory for wizard CSV uploads
- `./config.yaml` — created/updated by the wizard

No restart needed to add / edit / delete datasets; the registry hot-reloads.

## Option 3: Pre-populated `config.yaml` (advanced)

If you want to bake datasets into the image or restore a backup, edit `config.yaml` directly following `config.example.yaml`:

```yaml
app:
  contact_email: "contact@yourcompany.com"
  default_dataset: "acme"
datasets:
  acme:
    company:
      name: "Acme Corp"
      logo_url: "/static/images/acme_logo.png"
      # tagline accepts either a plain string (legacy) or a {fr, en} mapping.
      # The wizard always writes the dict form; users see the matching locale.
      tagline:
        fr: "Testez votre connaissance de vos collègues Acme."
        en: "Test your knowledge of your Acme colleagues."
    data:
      csv_path: "data/acme/team.csv"
      images_dir: "data/acme/photos"
      scores_db_path: "data/acme/scores.json"
      column_mapping:
        first_name: firstName
        last_name:  lastName
        photo:      photo_path
        team:       team
        job_title:  jobTitle
        company:    company
        sex:        sex
```

The **legacy single-dataset format** (top-level `company:` + `data:`) is auto-migrated on load to a single dataset named `default` — existing installs keep working without edits.

## Option 4: Cloud deployment

### Railway

1. Fork the repo on GitHub.
2. Create a new Railway project from your fork.
3. Set environment variables:
   - `SECRET_KEY` = random string
   - `FLASK_HOST` = `0.0.0.0`
   - `FLASK_PORT` = `$PORT`
   - `ADMIN_PASSWORD` = your admin password
4. Deploy → open the URL → follow the `/setup` wizard.

### Render

1. Fork the repo, create a Web Service from your fork.
2. Build command: `uv sync`
3. Start command: `uv run python app.py`
4. Add a **persistent disk mounted at `/app/data`** (required — otherwise datasets are wiped on redeploy).
5. Also persist `/app/config.yaml` (or mount it as a file env).
6. Set env vars (same as Railway).
7. Deploy → `/setup`.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | random | Flask session encryption key |
| `ADMIN_PASSWORD` | Strongly recommended | (none) | Password for `/setup*` routes. If unset, admin is wide open. |
| `APP_CONFIG` | No | `config.yaml` | Path to the config file |
| `UPLOAD_DIR` | No | `uploads` | Temp directory for wizard CSV uploads |
| `FLASK_DEBUG` | No | `false` | Enable debug mode (never in production) |
| `FLASK_HOST` | No | `127.0.0.1` | Bind address (`0.0.0.0` for Docker/cloud) |
| `FLASK_PORT` | No | `5000` | Port number |
| `UID` / `GID` | No (Docker) | `1000:1000` | Host UID/GID the container runs as. Export from your shell so bind-mounted files stay yours. |

## Admin authentication

- Visit `/setup`. If you're not logged in you're redirected to `/setup/login`, a standard HTML form. Enter `ADMIN_PASSWORD` and you're in for the session (signed cookie).
- Scripted callers can still pass `?password=...` in the query string to skip the form.
- **First-run bypass**: when no dataset is configured yet, `/setup` is reachable without auth so the very first dataset can be bootstrapped. Once a dataset exists, the password is required again.
- Log out via the button in the admin UI (POST `/setup/logout`) or by rotating `SECRET_KEY`.

## Switching Between Datasets

No restart. Two options:

- **UI**: dropdown in the header of every page (when ≥ 2 datasets exist).
- **Cookie**: `GET /dataset/<id>` sets the `dataset` cookie and invalidates any in-progress game.

Scores are scoped per dataset — a player's progress on Acme is independent from Client X.

## Updating Translations

After modifying template text:

```bash
make babel-extract       # Extract new strings into translations/messages.pot
# Edit translations/en/LC_MESSAGES/messages.po  (FR uses the msgid as source)
make babel-compile       # Compile .po → .mo
```

## Troubleshooting

**The app redirects me to /setup and nothing else works** — your registry is empty. By design: create the first dataset via the wizard to unlock the rest. Or run `make demo-dataset` and uncomment the `demo:` block in `config.yaml`.

**`/setup` returns `{"error": "Unauthorized"}`** — you're hitting a JSON client path with `ADMIN_PASSWORD` set. Either log in interactively via `/setup/login`, or append `?password=...` to the URL for scripted calls.

**"Missing required column mappings" during CSV save** — your mapping must cover the 7 required canonical fields (`first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`). The wizard enforces this; only trips you up when editing `config.yaml` by hand.

**`PermissionError: data/<id>/scores.json` on `make run` / `pytest`** — the dir was created by a pre-`user:` docker compose run and is root-owned. `sudo rm -rf data/<id>` then re-seed; compose now uses `${UID}:${GID}` so it won't happen again.

**`uv sync` fails with `Accès refusé` on `.venv\lib64`** — you mixed WSL and Windows on the same checkout. `rm -rf .venv` (WSL) or `cmd /c "rmdir /s /q .venv"` (PowerShell), then re-sync.

**Photos not rendering** — check that the `photo` column in the CSV contains filenames that exist under the dataset's `images_dir`. The per-employee *Modifier* page lets you re-upload photos one-by-one.

**Scores mixed between datasets** — shouldn't happen by design; each dataset has its own `data/<id>/scores.json`. If you see mixing, confirm the `dataset` cookie matches the dataset you think you're on.

**Validate your data**: `uv run python tools/validate_data.py` checks CSV columns and photo files for the active (default) dataset.
