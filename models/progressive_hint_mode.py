# models/progressive_hint_mode.py
from typing import Dict, Any, List, Optional
from .game_mode import GameMode
import random

class ProgressiveHintMode(GameMode):
    """
    Progressive Hint game mode where players get progressive hints about an employee
    and need to identify them as early as possible for more points.
    """
    @property
    def name(self) -> str:
        return "progressive_hint"

    @property
    def description(self) -> str:
        return "Mode indices progressifs : identifiez l'employé avec le moins d'indices possible pour gagner plus de points"

    @property
    def template(self) -> str:
        return "progressive_hint.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the progressive hint game mode.

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
            'max_score': len(employees) * 3  # Maximum 3 points per employee (if guessed with minimal hints)
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

        # Define the hints in order of increasing specificity
        hints = [
            {
                'level': 1,
                'text': f"Cette personne travaille chez {selected_employee['legalEntity_name']}",
                'points': 3  # Maximum points if guessed with just this hint
            },
            {
                'level': 2,
                'text': f"Cette personne fait partie de l'équipe {selected_employee['department_name']}",
                'points': 2  # Points if guessed with this hint
            },
            {
                'level': 3,
                'text': f"Cette personne occupe le poste de {selected_employee['jobTitle']}",
                'points': 1  # Minimum points if guessed with all hints
            }
        ]

        # Get choices for the employee (including the correct answer)
        # Filter by sex for more realistic choices
        sex_filter = {'sex': selected_employee['sex']}
        other_employees = self.game_manager.employee_data.get_filtered_employees(sex_filter)
        other_employees = [e for e in other_employees if e != selected_employee]

        # Select choices
        if len(other_employees) > 3:
            choices = random.sample(other_employees, 3)
        else:
            choices = other_employees

        # Add the correct answer
        choices.append(selected_employee)
        random.shuffle(choices)

        return {
            'game_over': False,
            'employee': selected_employee,
            'hints': hints,
            'choices': choices,
            'current_question': current_question,
            'total_questions': len(game_data)
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.

        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        correct_answer = kwargs.get('correct_answer', 0)
        hint_level = kwargs.get('hint_level', 3)  # Default to the maximum hint level (minimum points)

        if correct_answer:
            # Calculate points based on hint level
            # Fewer hints = more points
            if hint_level == 1:
                score_increment = 3
            elif hint_level == 2:
                score_increment = 2
            else:
                score_increment = 1

            # Update the score
            self.game_manager.score_manager.update_score(
                user_id, 
                score_increment=score_increment,
                company_correct=1 if hint_level >= 1 else 0,
                team_correct=1 if hint_level >= 2 else 0,
                name_correct=1,  # Always count as a correct name
                position_correct=1 if hint_level >= 3 else 0
            )
