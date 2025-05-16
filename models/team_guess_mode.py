# models/team_guess_mode.py
from typing import Dict, Any, List, Optional
from .game_mode import GameMode
import random

class TeamGuessMode(GameMode):
    """
    Team Guess game mode where players see an employee and need to guess which team they belong to.
    """
    @property
    def name(self) -> str:
        return "team_guess"

    @property
    def description(self) -> str:
        return "Mode équipe : devinez à quelle équipe appartient chaque employé"

    @property
    def template(self) -> str:
        return "team_guess.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the team guess game mode.

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
            'max_score': len(employees)  # 1 point per correct team guess
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

        # Get all unique teams for choices
        all_teams = self.game_manager.employee_data.get_unique_values('team')

        # Ensure the correct team is in the choices
        correct_team = selected_employee['team']
        if correct_team not in all_teams:
            all_teams.append(correct_team)

        # Select a subset of teams if there are too many
        if len(all_teams) > 4:
            # Make sure correct team is included
            other_teams = [team for team in all_teams if team != correct_team]
            selected_teams = random.sample(other_teams, 3)
            team_choices = selected_teams + [correct_team]
            random.shuffle(team_choices)
        else:
            team_choices = all_teams
            random.shuffle(team_choices)

        return {
            'game_over': False,
            'image_url': selected_employee['picture_href'],
            'name': selected_employee['name'],
            'position': selected_employee['position'],
            'correct_team': correct_team,
            'team_choices': team_choices,
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

        if correct_answer:
            # Update the score
            self.game_manager.score_manager.update_score(
                user_id, 
                score_increment=1,
                company_correct=0,
                team_correct=1,
                name_correct=0,
                position_correct=0
            )
