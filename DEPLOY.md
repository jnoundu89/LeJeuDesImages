# Deployment Guide

## Prerequisites

- Python 3.10+ (or Docker)
- Employee data: a CSV file + photos (see [docs/data-format.md](docs/data-format.md))

## Option 1: Local (development)

```bash
# 1. Clone and install
git clone https://github.com/<your-user>/LeJeuDesImages.git
cd LeJeuDesImages
uv sync

# 2. Configure
cp .env.example .env
cp config.example.yaml config.yaml

# Edit .env:
#   SECRET_KEY=<random-string>
#   ADMIN_PASSWORD=<your-admin-password>

# Edit config.yaml:
#   - Set company name, logo, email, tagline
#   - Set csv_path and images_dir
#   - Map your CSV columns to canonical fields

# 3. Place your data
mkdir -p data/photos
cp /path/to/your/team.csv data/team.csv
cp /path/to/your/photos/*.jpg data/photos/

# 4. Validate
uv run python tools/validate_data.py

# 5. Run
uv run python app.py
# -> http://127.0.0.1:5000
```

## Option 2: Docker

```bash
# 1. Clone
git clone https://github.com/<your-user>/LeJeuDesImages.git
cd LeJeuDesImages

# 2. Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your company settings

# 3. Place your data
mkdir -p data/photos
cp /path/to/your/team.csv data/team.csv
cp /path/to/your/photos/*.jpg data/photos/

# 4. Run
SECRET_KEY=my-secret docker compose up
# -> http://localhost:5000
```

Data persists via Docker volumes (`data/`, `config.yaml`, `scores_db.json`).

## Option 3: Setup Wizard (no manual config)

```bash
# 1. Start with defaults
docker compose up
# or: uv run python app.py

# 2. Open the setup wizard
# -> http://localhost:5000/setup

# 3. Follow the 4 steps:
#    Step 1: Company branding (name, logo, email)
#    Step 2: Upload CSV + map columns
#    Step 3: Upload photos (ZIP)
#    Step 4: Save

# 4. Restart the app to load the new config
```

## Option 4: Cloud deployment (Railway)

1. Fork the repo on GitHub
2. Go to [railway.app](https://railway.app) and create a new project from your fork
3. Set environment variables:
   - `SECRET_KEY` = a random string
   - `FLASK_HOST` = `0.0.0.0`
   - `FLASK_PORT` = `$PORT` (Railway sets this)
   - `ADMIN_PASSWORD` = your admin password
4. Deploy
5. Open `/setup` to configure your company data

## Option 5: Cloud deployment (Render)

1. Fork the repo on GitHub
2. Go to [render.com](https://render.com) and create a new Web Service from your fork
3. Build command: `uv sync`
4. Start command: `uv run python app.py`
5. Set environment variables (same as Railway)
6. Add a persistent disk mounted at `/app/data` for employee data
7. Deploy and open `/setup`

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | random | Flask session encryption key |
| `FLASK_DEBUG` | No | `false` | Enable debug mode (never in production) |
| `FLASK_HOST` | No | `127.0.0.1` | Bind address (`0.0.0.0` for Docker/cloud) |
| `FLASK_PORT` | No | `5000` | Port number |
| `ADMIN_PASSWORD` | No | (none) | Password for `/setup` wizard. If empty, setup is open |

## Switching Between Companies

The game supports multiple company configs. To switch:

```bash
# Keep multiple configs
cp config.yaml config.infolegale.yaml
cp config.yaml config.acme.yaml

# Switch by copying
cp config.acme.yaml config.yaml

# Restart the app
```

Or use the `/setup` wizard to reconfigure on the fly.

## Updating Translations

After modifying template text:

```bash
make babel-extract   # Extract new strings
# Edit translations/en/LC_MESSAGES/messages.po
make babel-compile   # Compile catalogs
```

## Troubleshooting

**"Config file not found"**: Copy `config.example.yaml` to `config.yaml`.

**Photos not showing**: Check that `data.images_dir` in `config.yaml` points to the correct directory and that photo paths in the CSV match the actual filenames.

**"Missing required column mappings"**: Your `config.yaml` column_mapping must include all 7 required fields. See `config.example.yaml`.

**Validate your setup**: Run `uv run python tools/validate_data.py` to check CSV columns and photo files.
