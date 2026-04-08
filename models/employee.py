# models/employee.py
import random
from typing import Any, Dict, List, Optional

import pandas as pd

from .config import CompanyConfig


class EmployeeData:
    """Loads employee data from CSV and normalizes column names via config mapping."""

    def __init__(self, config: CompanyConfig):
        self.config = config
        self.data = pd.read_csv(config.csv_path)

        # Rename CSV columns to canonical names (once, at load time)
        reverse_map = config.reverse_mapping()
        self.data.rename(columns=reverse_map, inplace=True)

    def get_all_employees(self) -> List[Dict[str, Any]]:
        return self.data.to_dict('records')

    def get_random_employees(self, count: int = 1) -> List[Dict[str, Any]]:
        return self.data.sample(n=count).to_dict('records')

    def get_filtered_employees(self, filter_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        filtered_data = self.data.copy()
        for column, value in filter_dict.items():
            filtered_data = filtered_data[filtered_data[column] == value]
        return filtered_data.to_dict('records')

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
