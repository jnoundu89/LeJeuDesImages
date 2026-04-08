# Lucca HR Importer

Reference implementation for importing employee data from the **Lucca HR API**, originally built for Infolegale.

## Files

| File | Description |
|------|-------------|
| `scraper.py` | Fetches employee IDs and details from the Lucca API, builds a simplified CSV |
| `csv_exporter.py` | Fetches and flattens full employee records into a detailed CSV |
| `generate_team.py` | Reads a Lucca CSV backup, downloads photos, and produces the final `infolegale_team.csv` |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LUCCA_AUTH_TOKEN` | Yes | Authentication token for the Lucca API (cookie-based) |
| `LUCCA_BASE_URL` | No | Base URL of the Lucca instance (default: `https://infolegale.ilucca.net`) |

## Usage

```bash
export LUCCA_AUTH_TOKEN="your-token-here"
python -m tools.importers.lucca.csv_exporter
```

## Writing a New Importer

To support a different HR system, create a new directory under `tools/importers/` (e.g., `tools/importers/bamboohr/`) and produce a CSV that matches the format described in `docs/data-format.md`.
