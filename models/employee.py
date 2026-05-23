# models/employee.py
import random
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional

import pandas as pd
from werkzeug.utils import secure_filename

from .config import CompanyConfig, DatasetConfig


def normalise_photo_value(value: Any) -> str:
    """Return the canonical ``/photos/<filename>`` form of a CSV photo value.

    The CSV authored by users is rarely consistent — values seen in the
    wild include::

        ``output/photos/alice.jpg``               # path inside their own export
        ``./photos/bob.png``                      # relative
        ``/photos/claire.png``                    # already canonical (demo)
        ``david.jpg``                             # bare filename
        ``\\\\unc\\share\\eve.png``               # Windows UNC path
        ``C:\\\\photos\\\\frank.jpg``             # Windows absolute
        ``197_Laurène_ANGELIN--BONNET.jpg``       # accents from a French export
        ``''`` / ``NaN``                          # missing

    All but the last collapse to ``/photos/<filename>`` so the
    server's ``/photos/<file>`` route + the templates' ``<img src>``
    work uniformly. NaN / empty / non-string returns ``''`` so callers
    can treat « no photo » as a falsy value.

    The basename is also passed through :func:`werkzeug.utils.secure_filename`
    so the CSV reference matches what the ZIP-extraction step produces
    on disk: both sides strip accents (Laurène → Laurene), drop
    non-ASCII, and normalise spaces. Without this step the two paths
    drift the moment a French name shows up and the « photo missing »
    check flags every accented row.

    Idempotent: ``normalise_photo_value('/photos/alice.jpg')`` ⟹
    ``'/photos/alice.jpg'``.
    """
    if value is None:
        return ''
    # pandas hands us float('nan') for blank CSV cells.
    try:
        if isinstance(value, float) and value != value:  # NaN check
            return ''
    except TypeError:
        pass
    if not isinstance(value, str):
        value = str(value)
    raw = value.strip()
    if not raw:
        return ''
    # Convert backslashes (Windows-style paths) into forward slashes
    # so PurePosixPath can split off the basename uniformly.
    name = PurePosixPath(raw.replace('\\', '/')).name
    # PurePosixPath('').name == ''  → guard against pathological inputs
    # like trailing slashes ("/photos/").
    if not name:
        return ''
    # Apply the same flattening the ZIP extractor uses so CSV refs and
    # on-disk filenames agree on accented + unicode names.
    safe = secure_filename(name)
    if not safe:
        return ''
    return '/photos/' + safe


class Employee(dict):
    """Dict subclass with computed properties for template convenience.

    Supports both dict access (employee['photo']) and attribute access
    (employee.full_name). Templates can use {{ emp.image_url }} and
    {{ emp.full_name }} without modes needing to enrich dicts manually.
    """

    @property
    def full_name(self) -> str:
        return f"{self.get('first_name', '')} {self.get('last_name', '')}".strip()

    @property
    def image_url(self) -> str:
        return self.get('photo', '')

    @property
    def name(self) -> str:
        return self.full_name

    @property
    def position(self) -> str:
        return self.get('job_title', '')

    @property
    def image_path(self) -> str:
        return self.get('photo', '')

    @property
    def id(self) -> str:
        return self.full_name


class EmployeeData:
    """Loads employee data from CSV and normalizes column names via config mapping."""

    def __init__(self, config: CompanyConfig | DatasetConfig):
        self.config = config
        self.data = pd.read_csv(config.csv_path)

        # Rename CSV columns to canonical names (once, at load time)
        reverse_map = config.reverse_mapping()
        self.data.rename(columns=reverse_map, inplace=True)

        # Normalise the photo column so any CSV — whether it stores
        # a bare filename, an `output/photos/X.jpg` export path, a
        # `/photos/X.jpg` URL or NaN — ends up as the canonical
        # `/photos/<filename>` form the route + templates expect.
        # Idempotent so re-loading is a no-op.
        if 'photo' in self.data.columns:
            self.data['photo'] = self.data['photo'].map(normalise_photo_value)

    @staticmethod
    def _to_employees(records: List[Dict[str, Any]]) -> List['Employee']:
        return [Employee(r) for r in records]

    def get_all_employees(self) -> List['Employee']:
        return self._to_employees(self.data.to_dict('records'))

    def get_random_employees(self, count: int = 1) -> List['Employee']:
        return self._to_employees(self.data.sample(n=count).to_dict('records'))

    def get_filtered_employees(self, filter_dict: Dict[str, Any]) -> List['Employee']:
        filtered_data = self.data.copy()
        for column, value in filter_dict.items():
            filtered_data = filtered_data[filtered_data[column] == value]
        # pandas' boolean-indexing narrows to DataFrame | Series; in practice
        # it's always DataFrame here so the to_dict overload is valid.
        return self._to_employees(filtered_data.to_dict('records'))  # type: ignore[call-overload,union-attr]

    def get_unique_values(self, column: str) -> List[Any]:
        return self.data[column].unique().tolist()

    def get_random_choices(self, column: str, correct_value: Any,
                           count: int = 4, filter_dict: Optional[Dict[str, Any]] = None) -> List[Any]:
        filtered_data = self.data.copy()
        if filter_dict:
            for filter_col, filter_val in filter_dict.items():
                filtered_data = filtered_data[filtered_data[filter_col] == filter_val]

        unique_values = filtered_data[column].unique().tolist()  # type: ignore[union-attr]

        # Robustness: when the optional filter narrows the pool below
        # what we need to build a multi-choice question (e.g. the
        # admin mapped `sex` to a column that's actually unique per
        # row, or the sex column is empty / free-text), fall back to
        # the unfiltered set so the player still gets options. Better
        # to relax the gender hint than to show a single answer.
        if filter_dict and len(unique_values) < count:
            unique_values = self.data[column].unique().tolist()

        if correct_value not in unique_values:
            unique_values.append(correct_value)

        if len(unique_values) <= count:
            return unique_values

        other_values = [v for v in unique_values if v != correct_value]
        selected = random.sample(other_values, count - 1)
        selected.append(correct_value)
        random.shuffle(selected)
        return selected

    # -- CRUD operations --

    def get_by_index(self, idx: int) -> 'Employee':
        if idx < 0 or idx >= len(self.data):
            raise IndexError(f'Employee index {idx} out of range')
        return Employee(self.data.iloc[idx].to_dict())

    def update_at_index(self, idx: int, fields: Dict[str, Any]) -> None:
        if idx < 0 or idx >= len(self.data):
            raise IndexError(f'Employee index {idx} out of range')
        for canonical_name, value in fields.items():
            if canonical_name in self.data.columns:
                # Normalise photo writes so an admin pasting a raw
                # filename / `output/photos/...` path through the
                # form ends up consistent with the rest of the data.
                if canonical_name == 'photo':
                    value = normalise_photo_value(value)
                self.data.at[self.data.index[idx], canonical_name] = value

    def append(self, fields: Dict[str, Any]) -> int:
        """Insert a new employee row; missing columns are filled with empty strings."""
        # Same photo-normalisation as `update_at_index` — applied here
        # so a freshly-added row is canonical without the caller knowing.
        if 'photo' in fields:
            fields = {**fields, 'photo': normalise_photo_value(fields['photo'])}
        row = {col: fields.get(col, '') for col in self.data.columns}
        # Ensure all mapped canonical fields land on the row even if they're not
        # yet present as DataFrame columns (e.g. adding manager_name to a CSV
        # that didn't originally have it).
        for k, v in fields.items():
            row.setdefault(k, v)
        new_df = pd.concat([self.data, pd.DataFrame([row])], ignore_index=True)
        self.data = new_df
        return len(self.data) - 1

    def delete_at_index(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.data):
            raise IndexError(f'Employee index {idx} out of range')
        self.data = self.data.drop(self.data.index[idx]).reset_index(drop=True)

    def save(self) -> None:
        """Write the DataFrame back to csv_path using the CSV column names."""
        mapping = self.config.column_mapping  # {canonical: csv_col}
        # Only rename columns that appear in both the mapping and the DataFrame
        rename_map = {k: v for k, v in mapping.items() if k in self.data.columns}
        self.data.rename(columns=rename_map).to_csv(self.config.csv_path, index=False)
