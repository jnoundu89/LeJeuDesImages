# models/employee.py
import pandas as pd
from typing import List, Dict, Any, Optional

class EmployeeData:
    """
    Class to handle employee data operations.
    """
    def __init__(self, csv_file_path: str):
        """
        Initialize the employee data from a CSV file.
        
        Args:
            csv_file_path: Path to the CSV file containing employee data
        """
        self.data = pd.read_csv(csv_file_path)
        
    def get_all_employees(self) -> List[Dict[str, Any]]:
        """
        Get all employees as a list of dictionaries.
        
        Returns:
            List of employee dictionaries
        """
        return self.data.to_dict('records')
    
    def get_random_employees(self, count: int = 1) -> List[Dict[str, Any]]:
        """
        Get a random sample of employees.
        
        Args:
            count: Number of random employees to return
            
        Returns:
            List of random employee dictionaries
        """
        return self.data.sample(n=count).to_dict('records')
    
    def get_filtered_employees(self, filter_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get employees filtered by the provided criteria.
        
        Args:
            filter_dict: Dictionary of column names and values to filter by
            
        Returns:
            List of filtered employee dictionaries
        """
        filtered_data = self.data.copy()
        for column, value in filter_dict.items():
            filtered_data = filtered_data[filtered_data[column] == value]
        return filtered_data.to_dict('records')
    
    def get_unique_values(self, column: str) -> List[Any]:
        """
        Get unique values for a specific column.
        
        Args:
            column: Column name to get unique values for
            
        Returns:
            List of unique values
        """
        return self.data[column].unique().tolist()
    
    def get_random_choices(self, column: str, correct_value: Any, 
                          count: int = 4, filter_dict: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Get random choices for a specific column, ensuring the correct value is included.
        
        Args:
            column: Column name to get choices for
            correct_value: The correct value that must be included in the choices
            count: Number of choices to return
            filter_dict: Optional dictionary to filter the data before selecting choices
            
        Returns:
            List of choices including the correct value
        """
        # Filter data if filter_dict is provided
        filtered_data = self.data.copy()
        if filter_dict:
            for filter_col, filter_val in filter_dict.items():
                filtered_data = filtered_data[filtered_data[filter_col] == filter_val]
        
        # Get unique values
        unique_values = filtered_data[column].unique().tolist()
        
        # Ensure correct_value is in the list
        if correct_value not in unique_values:
            unique_values.append(correct_value)
        
        # If we don't have enough unique values, return all we have
        if len(unique_values) <= count:
            return unique_values
        
        # Select random values excluding correct_value
        other_values = [v for v in unique_values if v != correct_value]
        import random
        selected = random.sample(other_values, count - 1)
        
        # Add correct_value and shuffle
        selected.append(correct_value)
        random.shuffle(selected)
        
        return selected