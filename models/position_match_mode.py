# models/position_match_mode.py
import random
from typing import Any, Dict, List, Optional

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class PositionMatchMode(GameMode):
    """
    Position Match game mode where players need to match employees with their correct positions.
    """
    @property
    def name(self) -> str:
        return "position_match"

    @property
    def description(self) -> str:
        return _l("Mode poste : associez chaque employé avec son poste correct")

    @property
    def template(self) -> str:
        return "position_match.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the position match game mode.

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

        # Select a subset of employees for the game (5 employees per round)
        selected_employees = employees[:5]

        # Store data and return initialization info
        data_id = self.game_manager.store_game_data({
            'all_employees': employees,
            'current_round_employees': selected_employees,
            'current_round': 1,
            'total_rounds': 3  # Play 3 rounds with different employees
        })

        return {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': 15  # 5 employees per round, 3 rounds
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
        # Get the game data
        game_data = self.game_manager.get_game_data(data_id)

        # Check if game is over
        current_round = game_data.get('current_round', 1)
        total_rounds = game_data.get('total_rounds', 3)

        if current_round > total_rounds:
            return {'game_over': True}

        # Get employees for the current round
        all_employees = game_data.get('all_employees', [])
        current_round_employees = game_data.get('current_round_employees', [])

        # If this is a new round, select new employees
        if len(used_indices) % 5 == 0 and len(used_indices) > 0:
            # Mark the current round as completed
            current_round += 1
            game_data['current_round'] = current_round

            if current_round > total_rounds:
                return {'game_over': True}

            # Select new employees for the next round
            start_index = (current_round - 1) * 5
            end_index = start_index + 5

            if end_index > len(all_employees):
                # Not enough employees for another round
                return {'game_over': True}

            current_round_employees = all_employees[start_index:end_index]
            game_data['current_round_employees'] = current_round_employees

        # Extract positions and shuffle them
        positions = [employee['job_title'] for employee in current_round_employees]
        shuffled_positions = positions.copy()
        random.shuffle(shuffled_positions)

        # Create a list of employees with their correct positions and shuffled positions
        employees_with_positions = []
        for i, employee in enumerate(current_round_employees):
            employees_with_positions.append({
                'employee': employee,
                'correct_position': employee['job_title'],
                'position_options': shuffled_positions
            })

        return {
            'game_over': False,
            'employees': employees_with_positions,
            'current_round': current_round,
            'total_rounds': total_rounds,
            'current_question': current_question
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.

        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        correct_matches = kwargs.get('correct_matches', 0)

        if correct_matches > 0:
            # Update the score
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=correct_matches,
                stat_updates={'position': correct_matches},
            )
