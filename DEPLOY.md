# Deployment Guide

The app boots without any config. On first launch with an empty or missing `config.yaml`, every route redirects to `/setup` so you can create your first dataset from the browser — zero YAML editing required.

## Prerequisites

- Python 3.10+ (or Docker)
- Per dataset: a CSV of employees + their photos. Columns are flexible; you map them to the canonical fields (`first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`, and optionally `birth_date`, `contract_start`, `manager_name`) from the wizard.

## Option 1: First-run wizard (recommended)

```bash
# 1. Clone and install
git clone https://github.com/<your-user>/LeJeuDesImages.git
cd LeJeuDesImages
uv sync

# 2. Minimal env
cp .env.example .env
# In .env set at least:
#   SECRET_KEY=<random-string>
#   ADMIN_PASSWORD=<pick-one>   # required to access /setup

# 3. Run — no config.yaml needed; you will create datasets from the UI
uv run python app.py
# -> http://127.0.0.1:5000  (redirects to /setup)

# 4. Follow the wizard
#    /setup           → "Ajouter un dataset"
#    step 1: dataset id + company branding
#    step 2: upload CSV + map columns
#    step 3: (edit) upload photos ZIP
#    step 4: review + save
#    → dataset is written to data/<id>/ and registered hot, no restart
```

To add more datasets, repeat step 4. Switch between them via the dataset dropdown in the header.

## Option 2: Docker

```bash
git clone https://github.com/<your-user>/LeJeuDesImages.git
cd LeJeuDesImages

# Minimal env for Docker
export SECRET_KEY=$(openssl rand -hex 32)
export ADMIN_PASSWORD=mypassword

docker compose up
# -> http://localhost:5000  (redirects to /setup)
```

Persisted volumes: `config.yaml` (auto-created by the wizard), `data/` (per-dataset CSV + photos + scores). No restart needed to add / edit / delete datasets.

## Option 3: Pre-populated config.yaml (advanced)

If you want to bake datasets into the image or restore a backup, edit `config.yaml` directly following `config.example.yaml`:

```yaml
app:
  contact_email: "contact@yourcompany.com"
  default_dataset: "acme"
datasets:
  acme:
    company: { name: "Acme Corp", logo_url: "/logo.png", tagline: "..." }
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

1. Fork the repo on GitHub
2. Create a new Railway project from your fork
3. Set environment variables:
   - `SECRET_KEY` = random string
   - `FLASK_HOST` = `0.0.0.0`
   - `FLASK_PORT` = `$PORT`
   - `ADMIN_PASSWORD` = your admin password
4. Deploy → open the URL → follow the `/setup` wizard

### Render

1. Fork the repo, create a Web Service from your fork
2. Build command: `uv sync`
3. Start command: `uv run python app.py`
4. Add a **persistent disk mounted at `/app/data`** (required — otherwise datasets are wiped on redeploy)
5. Also persist `/app/config.yaml` (or mount it as a file env)
6. Set env vars (same as Railway)
7. Deploy → `/setup`

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | random | Flask session encryption key |
| `ADMIN_PASSWORD` | Strongly recommended | (none) | Password for `/setup*` routes. If unset, admin is wide open |
| `APP_CONFIG` | No | `config.yaml` | Path to the config file |
| `UPLOAD_DIR` | No | `uploads` | Temp directory for wizard CSV uploads |
| `FLASK_DEBUG` | No | `false` | Enable debug mode (never in production) |
| `FLASK_HOST` | No | `127.0.0.1` | Bind address (`0.0.0.0` for Docker/cloud) |
| `FLASK_PORT` | No | `5000` | Port number |

## Switching Between Datasets

No restart. Two options:

- **UI**: dropdown in the header of every page (when ≥ 2 datasets exist)
- **Cookie**: `GET /dataset/<id>` sets the `dataset` cookie (also invalidates any in-progress game)

Scores are scoped per dataset — a player's progress on Acme is independent from Client X.

## Updating Translations

After modifying template text:

```bash
make babel-extract       # Extract new strings into translations/messages.pot
# Edit translations/en/LC_MESSAGES/messages.po  (FR uses the msgid as source)
make babel-compile       # Compile .po → .mo
```

## Troubleshooting

**The app redirects me to /setup and nothing else works**: your registry is empty — by design, create the first dataset via the wizard to unlock the rest.

**"Missing required column mappings" during CSV save**: your mapping must cover the 7 required canonical fields (`first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`). The wizard enforces this; only trips you up when editing `config.yaml` by hand.

**Photos not rendering**: check that the `photo` column in the CSV contains filenames that exist under the dataset's `images_dir`. The per-employee *Modifier* page lets you re-upload photos one-by-one.

**Scores mixed between datasets**: shouldn't happen by design — each dataset has its own `data/<id>/scores.json`. If you see mixing, confirm the cookie `dataset` matches the dataset you think you're on.

**Validate your data**: `uv run python tools/validate_data.py` checks CSV columns and photo files for the active (default) dataset.
