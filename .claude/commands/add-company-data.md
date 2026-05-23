---
name: add-company-data
description: Set up a new company dataset (CSV + photos + config) without touching code
---

# Add Company Data

Guide to switch the game to a new company's data.

## Steps

1. **Prepare the CSV**: Place the employee CSV file at `data/team.csv`
   - Required columns: first_name, last_name, photo path, team, job_title, company, sex
   - Optional: birth_date, contract_start, manager_name
   - Column names can be anything -- the mapping is in config.yaml

2. **Prepare the photos**: Place employee photos in `data/photos/`
   - Formats: JPG, PNG
   - The `photo` column in CSV should match the filenames (e.g., `/photos/alice.jpg`)

3. **Create config.yaml** from the example:
   ```bash
   cp config.example.yaml config.yaml
   ```

4. **Edit config.yaml**:
   - `company.name`: your company name
   - `company.logo_url`: URL or path to your logo
   - `company.contact_email`: contact email
   - `data.csv_path`: path to CSV (default: `data/team.csv`)
   - `data.images_dir`: path to photos (default: `data/photos`)
   - `data.column_mapping`: map YOUR CSV columns to canonical names

5. **Validate**:
   ```bash
   uv run python tools/validate_data.py
   ```

6. **Test**: Start the app and play a round to verify.

## Switching between companies

Keep multiple configs:
```bash
cp config.yaml config.acme.yaml     # save current
cp config.other.yaml config.yaml    # switch
```

Or use the `/setup` wizard at `http://localhost:5000/setup`.
