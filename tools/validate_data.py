#!/usr/bin/env python3
"""Validate employee data and photos against config.yaml."""
import sys
from pathlib import Path

# Add project root to path so we can import models
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from models.config import OPTIONAL_FIELDS, REQUIRED_FIELDS, CompanyConfig


def main():
    config_path = PROJECT_ROOT / 'config.yaml'
    print(f'Loading config from {config_path} ...')

    try:
        config = CompanyConfig(str(config_path))
    except (FileNotFoundError, ValueError) as exc:
        print(f'ERROR: {exc}')
        sys.exit(1)

    print(f'Company: {config.company_name}')
    print(f'CSV path: {config.csv_path}')
    print(f'Images dir: {config.images_dir}')
    print()

    # -- Load CSV --
    csv_path = PROJECT_ROOT / config.csv_path
    if not csv_path.exists():
        print(f'ERROR: CSV file not found: {csv_path}')
        sys.exit(1)

    df = pd.read_csv(csv_path)
    print(f'Loaded {len(df)} rows from {csv_path}')
    print()

    mapping = config.column_mapping
    errors: list[str] = []
    warnings: list[str] = []

    # -- Check required columns --
    print('--- Required columns ---')
    for canonical, csv_col in mapping.items():
        if canonical not in REQUIRED_FIELDS:
            continue
        if csv_col in df.columns:
            non_null = df[csv_col].notna().sum()
            print(f'  OK  {canonical} -> "{csv_col}" ({non_null}/{len(df)} non-null)')
        else:
            msg = f'MISSING required column: {canonical} -> "{csv_col}" not found in CSV'
            errors.append(msg)
            print(f'  ERR {msg}')
    print()

    # -- Check optional columns --
    print('--- Optional columns ---')
    for canonical in OPTIONAL_FIELDS:
        csv_col = mapping.get(canonical)
        if csv_col is None:
            msg = f'{canonical}: not configured in column_mapping'
            warnings.append(msg)
            print(f'  WARN {msg}')
        elif csv_col in df.columns:
            non_null = df[csv_col].notna().sum()
            print(f'  OK   {canonical} -> "{csv_col}" ({non_null}/{len(df)} non-null)')
        else:
            msg = f'{canonical} -> "{csv_col}" configured but column not found in CSV'
            warnings.append(msg)
            print(f'  WARN {msg}')
    print()

    # -- Check photos --
    photo_col = mapping.get('photo')
    photos_found = 0
    photos_missing = 0

    if photo_col and photo_col in df.columns:
        print('--- Photo validation ---')
        PROJECT_ROOT / config.images_dir
        for idx, row in df.iterrows():
            photo_val = row[photo_col]
            if pd.isna(photo_val) or not str(photo_val).strip():
                msg = f'Row {idx}: empty photo path'
                errors.append(msg)
                photos_missing += 1
                continue

            photo_str = str(photo_val).strip()

            # Handle paths that start with / (relative to app root, e.g. /static/images/foo.jpg)
            if photo_str.startswith('/'):
                photo_path = PROJECT_ROOT / photo_str.lstrip('/')
            else:
                photo_path = PROJECT_ROOT / photo_str

            if photo_path.exists():
                photos_found += 1
            else:
                msg = f'Row {idx}: photo not found: {photo_path}'
                errors.append(msg)
                photos_missing += 1

        print(f'  Photos found:   {photos_found}')
        print(f'  Photos missing: {photos_missing}')
    else:
        errors.append('Cannot validate photos: photo column not available')
    print()

    # -- Summary --
    print('=' * 50)
    print('SUMMARY')
    print('=' * 50)
    print(f'Employees loaded:  {len(df)}')
    print(f'Photos found:      {photos_found}')
    print(f'Photos missing:    {photos_missing}')
    print(f'Warnings:          {len(warnings)}')
    print(f'Errors:            {len(errors)}')
    print()

    if errors:
        print(f'{len(errors)} error(s) detected. Fix them before running the game.')
        # Only print first 20 errors to avoid flooding the terminal
        for e in errors[:20]:
            print(f'  - {e}')
        if len(errors) > 20:
            print(f'  ... and {len(errors) - 20} more')
        sys.exit(1)
    else:
        print('All checks passed.')


if __name__ == '__main__':
    main()
