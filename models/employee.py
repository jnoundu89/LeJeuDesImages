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
        return self._to_employees(filtered_data.to_dict('records'))

    def get_unique_values(self, column: str) -> List[Any]:
        return self.data[column].unique().tolist()

    def get_random_choices(self, column: str, correct_value: Any,
                           count: int = 4, filter_dict: Optional[Dict[str, Any]] = None) -> List[Any]:
        filtered_data = self.data.copy()
        if filter_dict:
            for filter_col, filter_val in filter_dict.items():
                filtered_data = filtered_data[filtered_data[filter_col] == filter_val]

        unique_values = filtered_data[column].unique().tolist()

        if correct_value not in unique_values:
            unique_values.append(correct_value)

        if len(unique_values) <= count:
            return unique_values

        other_values = [v for v in unique_values if v != correct_value]
        selected = random.sample(other_values, count - 1)
        selected.append(correct_value)
        random.shuffle(selected)
        return selected
