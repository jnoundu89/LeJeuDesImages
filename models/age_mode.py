# models/age_mode.py
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class AgeMode(GameMode):
    """
    Age game mode where players need to identify the age of an employee.
    This mode uses the birth_date field to calculate the age and offers 3 other choices
    at +/- 5 years from the real age.
    """
    @property
    def name(self) -> str:
        return "age"

    @property
    def description(self) -> str:
        return _l("Quel âge a la personne ? Devinez l'âge de la personne affichée")

    @property
    def template(self) -> str:
        return "age.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the age game mode.

        Args:
            user_id: Optional user ID. If not provided, a new user will be created.

        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id)

        # Get all employees
        all_employees = self.game_manager.employee_data.get_all_employees()

        # Filter employees with a birth date
        employees_with_birth_date = [emp for emp in all_employees if emp.get('birth_date')]

        # Store data and return initialization info
        data_id = self.game_manager.store_game_data(employees_with_birth_date)

        return {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': len(employees_with_birth_date)  # 1 point per correct age
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
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        selected_employee = selected

        # Calculate age
        birth_date_str = selected_employee.get('birth_date')
        if not birth_date_str:
            # If no birth date, skip this question
            return self.get_question_data(data_id, used_indices, current_question - 1)

        try:
            birth_date = datetime.strptime(birth_date_str.split('T')[0], '%Y-%m-%d')
            current_date = datetime.now()
            age = current_date.year - birth_date.year

            # Adjust for month and day
            if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
                age -= 1

            # Generate 3 other options (different from the correct one)
            # These should be +/- 5 years from the real age
            other_options = []
            while len(other_options) < 3:
                # Generate a random age within +/- 5 years of the real age
                option = age + random.randint(-5, 5)
                # Ensure age is positive and different from the correct one
                if option > 0 and option != age and option not in other_options:
                    other_options.append(option)

            # Add the correct answer
            choices = other_options + [age]
            random.shuffle(choices)

            return {
                'game_over': False,
                'employee': selected_employee,
                'age': age,
                'choices': choices,
                'current_question': current_question,
                'total_questions': len(self.game_manager.get_game_data(data_id))
            }
        except Exception as e:
            # If error parsing date, skip this question
            print(f"Error calculating age: {e}")
            return self.get_question_data(data_id, used_indices, current_question - 1)

    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.

        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        correct_answer = kwargs.get('correct_answer', 0)

        if correct_answer:
            # Update the score
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=1,
                stat_updates={'name': 1},
            )
