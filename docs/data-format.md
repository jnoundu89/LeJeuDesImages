# Data Format

## CSV File

The game reads employee data from a CSV file. The path is configured in `config.yaml` under `data.csv_path`.

### Required Columns

Your CSV must contain columns that map to these canonical fields (configure the mapping in `config.yaml` under `data.column_mapping`):

| Canonical Field | Description | Example |
|----------------|-------------|---------|
| `first_name` | Employee first name | "Alice" |
| `last_name` | Employee last name | "DUPONT" |
| `photo` | Path to employee photo (relative to app root) | "/static/images/alice_dupont.jpg" |
| `team` | Department or team name | "Engineering" |
| `job_title` | Job title | "Software Engineer" |
| `company` | Company or legal entity name | "Acme Corp" |
| `sex` | Gender ("man" or "woman") - used for name choice filtering | "woman" |

### Optional Columns

| Canonical Field | Description | Used By |
|----------------|-------------|---------|
| `birth_date` | Birth date (ISO format: YYYY-MM-DDThh:mm:ss) | Age mode |
| `contract_start` | Contract start date (ISO format) | Seniority mode |
| `manager_name` | Manager's full name | Manager mode, Clue mode |

## Photos

Place employee photos in the directory configured in `config.yaml` under `data.images_dir` (default: `static/images`).

- Supported formats: JPG, PNG
- Recommended size: 400x400px minimum
- Naming convention: any consistent scheme (e.g., `firstname_lastname.jpg`)

## Configuration

See `config.example.yaml` for a complete example of the configuration file.

## Validation

Run the data validation tool to check your setup:

```bash
python tools/validate_data.py
```
