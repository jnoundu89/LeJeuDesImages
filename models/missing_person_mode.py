# models/missing_person_mode.py
import random
from typing import Any, Dict, List, Optional

from .game_mode import GameMode


class MissingPersonMode(GameMode):
    """
    Missing Person game mode where players see a group of employees with one missing,
    and need to identify who's missing from a specific team.
    """
    @property
    def name(self) -> str:
        return "missing_person"

    @property
    def description(self) -> str:
        return "Mode personne manquante : identifiez qui manque dans l'équipe affichée"

    @property
    def template(self) -> str:
        return "missing_person.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the missing person game mode.

        Args:
            user_id: Optional user ID. If not provided, a new user will be created.

        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id)

        # Get all employees
        all_employees = self.game_manager.employee_data.get_all_employees()

        # Group employees by team
        teams = {}
        for employee in all_employees:
            team = employee.get('team', 'Unknown')
            if team not in teams:
                teams[team] = []
            teams[team].append(employee)

        # Filter teams with at least 4 members (so we can show 3 and hide 1)
        valid_teams = {team: members for team, members in teams.items() if len(members) >= 4}

        # If no valid teams, use all employees
        if not valid_teams:
            game_data = {
                'all_employees': all_employees,
                'teams': {'All': all_employees}
            }
        else:
            game_data = {
                'all_employees': all_employees,
                'teams': valid_teams
            }

        # Store data and return initialization info
        data_id = self.game_manager.store_game_data(game_data)

        # Calculate max score based on number of valid teams
        max_score = sum(1 for team in valid_teams.values() for _ in team)

        return {
            'user_id': user_id,
            'data_id': data_id,
            'reverse_mode': False,
            'max_score': max_score  # 1 point per correct missing person
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

        # Get all teams
        teams = game_data.get('teams', {})
        all_employees = game_data.get('all_employees', [])

        # If no teams or all questions used, game over
        if not teams or len(used_indices) >= len(all_employees):
            return {'game_over': True}

        # Select a random team with at least 4 members
        valid_teams = [team for team, members in teams.items() if len(members) >= 4]

        # If no valid teams left, game over
        if not valid_teams:
            return {'game_over': True}

        # Select a random team
        selected_team = random.choice(valid_teams)
        team_members = teams[selected_team]

        # Select a random member to be the "missing person"
        missing_person = random.choice(team_members)

        # Make sure we haven't used this person before
        missing_index = all_employees.index(missing_person)
        attempts = 0
        while missing_index in used_indices and attempts < 10:
            missing_person = random.choice(team_members)
            missing_index = all_employees.index(missing_person)
            attempts += 1

        # If we couldn't find an unused person after 10 attempts, game over
        if missing_index in used_indices:
            return {'game_over': True}

        # Mark this index as used
        used_indices.append(missing_index)
        current_question += 1

        # Select other team members to display (excluding the missing person)
        other_members = [m for m in team_members if m != missing_person]
        if len(other_members) > 3:
            displayed_members = random.sample(other_members, 3)
        else:
            displayed_members = other_members

        # Get choices for the missing person (including the correct answer)
        # Filter by sex for more realistic choices
        sex_filter = {'sex': missing_person['sex']}
        other_employees = [e for e in all_employees if e['team'] == selected_team and e != missing_person]

        # If not enough team members for choices, include employees from other teams
        if len(other_employees) < 3:
            additional_employees = self.game_manager.employee_data.get_filtered_employees(sex_filter)
            additional_employees = [e for e in additional_employees if e not in other_employees and e != missing_person]
            if additional_employees:
                other_employees.extend(random.sample(additional_employees, min(3 - len(other_employees), len(additional_employees))))

        # Select choices
        if len(other_employees) > 3:
            choices = random.sample(other_employees, 3)
        else:
            choices = other_employees

        # Add the correct answer
        choices.append(missing_person)
        random.shuffle(choices)

        return {
            'game_over': False,
            'team_name': selected_team,
            'displayed_members': displayed_members,
            'missing_person': missing_person,
            'choices': choices,
            'current_question': current_question,
            'total_questions': len(all_employees)
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
                stat_updates={'team': 1, 'name': 1}
            )
