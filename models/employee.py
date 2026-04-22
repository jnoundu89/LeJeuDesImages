# models/employee.py
import random
from typing import Any, Dict, List, Optional

import pandas as pd

from .config import CompanyConfig, DatasetConfig


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
                self.data.at[self.data.index[idx], canonical_name] = value

    def append(self, fields: Dict[str, Any]) -> int:
        """Insert a new employee row; missing columns are filled with empty strings."""
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
