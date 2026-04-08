# models/example_mode.py
from typing import Any, Dict, List, Optional

from .game_mode import GameMode


class ExampleMode(GameMode):
    """
    Example game mode to demonstrate how to add a new game mode.
    This mode is a simplified version of the normal mode where users only need to identify the name.
    """
    @property
    def name(self) -> str:
        return "example"

    @property
    def description(self) -> str:
        return "Mode exemple : identifiez uniquement le nom de la personne sur l'image"

    @property
    def template(self) -> str:
        return "example.html"  # This template would need to be created

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the example game mode.

        Args:
            user_id: Optional user ID. If not provided, a new user will be created.

        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id)

        # Get all employees
        employees = self.game_manager.employee_data.get_all_employees()

        # Store data and return initialization info
        data_id = self.game_manager.store_game_data(employees)

        return {
            'user_id': user_id,
            'data_id': data_id,
            'reverse_mode': False,  # Not a reverse mode
            'max_score': len(employees)  # 1 question (name only) per employee
        }

    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        """
        Get data for the current question.

        Args:
            data_id: ID of the game data
            used_indices: List of indices that have already been used
            current_question: Current question number

        Returns:
            Dictionary with question data
        """
        # Use the game manager to get question data (with reverse_mode=False)
        question_data = self.game_manager.get_question_data(data_id, used_indices, current_question, False)

        # If game is over, return that info
        if question_data.get('game_over', False):
            return question_data

        # Simplify the data for this mode (we only care about the name)
        selected_employee = question_data.get('correct_values', {})

        # Get choices for name only, filtered by sex
        sex_filter = {'sex': question_data.get('sex', 'man')}  # Default to 'man' if sex is not provided
        names = self.game_manager.employee_data.get_random_choices(
            'name',
            selected_employee.get('name', ''),
            filter_dict=sex_filter
        )

        return {
            'game_over': False,
            'image_url': question_data.get('image_url', ''),
            'correct_name': selected_employee.get('name', ''),
            'name_choices': names,
            'current_question': current_question
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.

        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        # In this mode, we only care about the name
        correct_answer = kwargs.get('correct_answer', 0)

        if correct_answer:
            # Update the score and name statistic
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=1,
                stat_updates={'name': 1},
            )
