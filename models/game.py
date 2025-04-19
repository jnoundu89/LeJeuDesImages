# models/game.py
from typing import Dict, Any, List, Optional
import random
import pandas as pd
from .employee import EmployeeData
from .score import ScoreManager

class GameManager:
    """
    Class to handle game logic for different game modes.
    """
    def __init__(self, employee_data: EmployeeData, score_manager: ScoreManager):
        """
        Initialize the game manager.

        Args:
            employee_data: EmployeeData instance for accessing employee data
            score_manager: ScoreManager instance for managing scores
        """
        self.employee_data = employee_data
        self.score_manager = score_manager
        self.game_data_cache = {}

    def store_game_data(self, data: List[Dict[str, Any]]) -> int:
        """
        Store game data in the cache and return a unique ID.

        Args:
            data: List of employee dictionaries to store

        Returns:
            Unique ID for the stored data
        """
        data_id = random.randint(1000, 9999)
        self.game_data_cache[data_id] = data
        return data_id

    def get_game_data(self, data_id: int) -> List[Dict[str, Any]]:
        """
        Get game data from the cache.

        Args:
            data_id: ID of the data to retrieve

        Returns:
            List of employee dictionaries
        """
        return self.game_data_cache.get(data_id, [])

    def initialize_normal_mode(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the normal game mode.

        Args:
            user_id: Optional user ID. If not provided, a new user will be created.

        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.score_manager.initialize_user(user_id)

        # Get all employees in random order
        employees = self.employee_data.get_all_employees()
        random.shuffle(employees)

        # Store data and return initialization info
        data_id = self.store_game_data(employees)

        return {
            'user_id': user_id,
            'data_id': data_id,
            'reverse_mode': False,
            'max_score': len(employees) * 4  # 4 questions per employee
        }

    def initialize_reverse_mode(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the reverse game mode.

        Args:
            user_id: Optional user ID. If not provided, a new user will be created.

        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.score_manager.initialize_user(user_id)

        # Get all employees in random order
        employees = self.employee_data.get_all_employees()
        random.shuffle(employees)

        # Store data and return initialization info
        data_id = self.store_game_data(employees)

        return {
            'user_id': user_id,
            'data_id': data_id,
            'reverse_mode': True,
            'max_score': len(employees)  # 1 question per employee in reverse mode
        }

    def get_question_data(self, data_id: int, used_indices: List[int], 
                         current_question: int, reverse_mode: bool) -> Dict[str, Any]:
        """
        Get data for the current question.

        Args:
            data_id: ID of the game data
            used_indices: List of indices that have already been used
            current_question: Current question number
            reverse_mode: Whether the game is in reverse mode

        Returns:
            Dictionary with question data
        """
        # Get game data
        game_data = self.get_game_data(data_id)

        # If all indices have been used, return None
        if len(used_indices) >= len(game_data):
            return {'game_over': True}

        # Get all available indices
        all_indices = list(range(len(game_data)))
        available_indices = [i for i in all_indices if i not in used_indices]

        if not available_indices:
            return {'game_over': True}

        # Get the next index
        index = available_indices[0]
        used_indices.append(index)
        current_question += 1

        # Get the selected employee
        selected_employee = game_data[index]

        # Prepare question data based on game mode
        if reverse_mode:
            return self._prepare_reverse_mode_question(selected_employee, game_data, current_question)
        else:
            return self._prepare_normal_mode_question(selected_employee, game_data, current_question)

    def _prepare_normal_mode_question(self, selected_employee: Dict[str, Any], 
                                     game_data: List[Dict[str, Any]], 
                                     current_question: int) -> Dict[str, Any]:
        """
        Prepare data for a normal mode question.

        Args:
            selected_employee: The selected employee dictionary
            game_data: The full game data
            current_question: Current question number

        Returns:
            Dictionary with question data
        """
        # Get correct values
        correct_values = {
            'company': selected_employee['company'],
            'team': selected_employee['team'],
            'name': selected_employee['name'],
            'position': selected_employee['position']
        }

        # Get choices for each category
        companies = ['Infolegale', 'Eloficash']  # Fixed options

        # For team, name, and position, filter by sex for more realistic choices
        sex_filter = {'sex': selected_employee['sex']}

        teams = self.employee_data.get_random_choices('team', correct_values['team'])
        names = self.employee_data.get_random_choices('name', correct_values['name'], filter_dict=sex_filter)
        positions = self.employee_data.get_random_choices('position', correct_values['position'], filter_dict=sex_filter)

        return {
            'game_over': False,
            'image_url': selected_employee['image_url'],
            'correct_values': correct_values,
            'choices': {
                'companies': companies,
                'teams': teams,
                'names': names,
                'positions': positions
            },
            'current_question': current_question
        }

    def _prepare_reverse_mode_question(self, selected_employee: Dict[str, Any], 
                                      game_data: List[Dict[str, Any]], 
                                      current_question: int) -> Dict[str, Any]:
        """
        Prepare data for a reverse mode question.

        Args:
            selected_employee: The selected employee dictionary
            game_data: The full game data
            current_question: Current question number

        Returns:
            Dictionary with question data
        """
        # In reverse mode, we show the name and ask to identify the person
        correct_value = selected_employee['name']

        # Filter employees by sex for more realistic choices
        sex_filter = {'sex': selected_employee['sex']}
        filtered_employees = self.employee_data.get_filtered_employees(sex_filter)

        # Select 3 random employees of the same sex (plus the correct one)
        other_employees = [e for e in filtered_employees if e['name'] != correct_value]
        if len(other_employees) > 3:
            other_employees = random.sample(other_employees, 3)

        # Combine with the correct employee
        choices = [selected_employee] + other_employees
        random.shuffle(choices)

        # Convert choices to a pandas DataFrame for compatibility with the template
        choices_df = pd.DataFrame(choices)

        return {
            'game_over': False,
            'correct_value': correct_value,
            'choices': choices_df,
            'current_question': current_question
        }

    def update_score_normal_mode(self, user_id: int, score_increment: int, 
                               company_correct: int = 0, team_correct: int = 0, 
                               name_correct: int = 0, position_correct: int = 0) -> None:
        """
        Update score for normal mode.

        Args:
            user_id: The user ID
            score_increment: The amount to increment the score by
            company_correct: Whether the company answer was correct (0 or 1)
            team_correct: Whether the team answer was correct (0 or 1)
            name_correct: Whether the name answer was correct (0 or 1)
            position_correct: Whether the position answer was correct (0 or 1)
        """
        self.score_manager.update_score(
            user_id, score_increment, company_correct, team_correct, name_correct, position_correct
        )

    def update_score_reverse_mode(self, user_id: int, correct_answer: int) -> None:
        """
        Update score for reverse mode.

        Args:
            user_id: The user ID
            correct_answer: Whether the answer was correct (0 or 1)
        """
        self.score_manager.update_score_reverse_mode(user_id, correct_answer)

    def get_result_data(self, user_id: int, max_score: int, total_questions: int) -> Dict[str, Any]:
        """
        Get data for the result page.

        Args:
            user_id: The user ID
            max_score: The maximum possible score
            total_questions: The total number of questions answered

        Returns:
            Dictionary with result data
        """
        user_score = self.score_manager.get_user_score(user_id)
        stats = self.score_manager.get_stats(user_id)

        return {
            'score': user_score['score'],
            'max_score': max_score,
            'current_score': user_score['score'],
            'total_questions': total_questions,
            'stats': stats
        }
