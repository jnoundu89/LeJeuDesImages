# models/timed_mode.py
from typing import Dict, Any, List, Optional
from .game_mode import GameMode
import random

class TimedMode(GameMode):
    """
    Timed game mode where players must identify the maximum number of people in a limited time (2 minutes).
    The final score depends on the number of people correctly identified.
    """
    @property
    def name(self) -> str:
        return "timed"

    @property
    def description(self) -> str:
        return "Mode chronométré : identifiez le maximum de personnes en 2 minutes"

    @property
    def template(self) -> str:
        return "timed.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the timed game mode.

        Args:
            user_id: Optional user ID. If not provided, a new user will be created.

        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id)

        # Get all employees
        employees = self.game_manager.employee_data.get_all_employees()
        random.shuffle(employees)

        # Store data and return initialization info
        data_id = self.game_manager.store_game_data(employees)

        return {
            'user_id': user_id,
            'data_id': data_id,
            'reverse_mode': False,
            'max_score': len(employees)  # 1 point per correctly identified employee
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

        # Get the selected employee data
        selected_employee = question_data.get('correct_values', {})

        # Get choices for name, filtered by sex
        sex_filter = {'sex': selected_employee.get('sex', 'man')}  # Default to 'man' if sex is not provided
        # Safely access firstName and lastName
        first_name = selected_employee.get('firstName', '')
        last_name = selected_employee.get('lastName', '')
        # Create full name by joining firstName and lastName
        full_name = f"{first_name} {last_name}"

        # Get random first names and create full names for choices
        first_names = self.game_manager.employee_data.get_random_choices(
            'firstName',
            first_name,  # Use the safely accessed first_name variable
            filter_dict=sex_filter
        )

        # Create a list of full names, ensuring the correct one is included
        names = [full_name]
        correct_first_name = first_name  # Store the correct first name
        for name in first_names:
            if name != correct_first_name:
                names.append(f"{name} {last_name}")  # Use the safely accessed last_name
                if len(names) >= 4:  # Limit to 4 choices
                    break

        # Shuffle the names to randomize the order
        random.shuffle(names)

        return {
            'game_over': False,
            'image_url': question_data.get('image_url', ''),
            'correct_name': full_name,
            'name_choices': names,
            'current_question': current_question,
            'total_time': 120,  # 2 minutes in seconds
            'correct_values': selected_employee
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
                company_correct=0,
                team_correct=0,
                name_correct=1,
                position_correct=0
            )
