# models/manager_mode.py
import random
from typing import Any, Dict, List, Optional

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class ManagerMode(GameMode):
    """
    Manager game mode where players need to identify who is the manager of a given employee.
    This mode is inspired by the reverse mode but with 4 images.
    """
    @property
    def name(self) -> str:
        return "manager"

    @property
    def display_name(self):
        return _l("Manager")

    @property
    def description(self):
        return _l("Qui est le manager de qui ? Identifiez le manager de la personne affichée")

    @property
    def template(self) -> str:
        return "manager.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the manager game mode.

        Args:
            user_id: Optional user ID. If not provided, a new user will be created.

        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id)

        # Get all employees
        all_employees = self.game_manager.employee_data.get_all_employees()

        # Filter employees with a manager
        employees_with_manager = [emp for emp in all_employees if emp.get('manager_name')]

        # Store data and return initialization info
        data_id = self.game_manager.store_game_data(employees_with_manager)

        return {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': len(employees_with_manager)  # 1 point per correct manager
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
        selected_employee, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected_employee.get('game_over'):
            return selected_employee

        manager_name = selected_employee.get('manager_name', '')

        # Find the manager in the employee list by name
        all_employees = self.game_manager.employee_data.get_all_employees()
        manager = next(
            (emp for emp in all_employees if emp.full_name == manager_name),
            None
        )

        if not manager:
            # If manager not found, skip this question
            return self.get_question_data(data_id, used_indices, current_question - 1)

        # Get 3 other random employees as wrong choices
        other_employees = [emp for emp in all_employees
                          if emp.full_name != manager_name
                          and emp != selected_employee]

        if len(other_employees) >= 3:
            choices = random.sample(other_employees, 3)
        else:
            choices = list(other_employees)

        # Add the correct answer
        choices.append(manager)
        random.shuffle(choices)

        return {
            'game_over': False,
            'employee': selected_employee,
            'manager': manager,
            'choices': choices,
            'current_question': current_question,
            'total_questions': len(self.game_manager.get_game_data(data_id))
        }

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
                stat_updates={'team': 1, 'position': 1},
            )
