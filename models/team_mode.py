# models/team_mode.py
import random
from typing import Any, ClassVar, Dict, List, Optional

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class TeamMode(GameMode):
    """
    Team game mode where players must identify all members of a specific team.
    A team photo is displayed, and the player must associate names with faces.
    """

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name', 'sex', 'team']
    difficulty: ClassVar[int] = 2
    estimated_duration_sec: ClassVar[int] = 180
    tags: ClassVar[List[str]] = ['culture', 'photo']
    icon: ClassVar[str] = 'fa-people-group'
    preview_type: ClassVar[str] = 'static'

    @property
    def name(self) -> str:
        return "team"

    @property
    def display_name(self):
        return _l("Équipe")

    @property
    def description(self):
        return _l("Mode équipe : identifiez tous les membres d'une équipe spécifique")

    @property
    def template(self) -> str:
        return "team.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the team game mode.

        Args:
            user_id: Optional user ID. If not provided, a new user will be created.

        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id, mode=self.name)

        # Get eligible employees (with required fields populated)
        all_employees = self.game_manager.employee_data.get_all_employees()
        employees = self.eligible_employees(all_employees)

        # Group employees by team
        teams = {}
        for employee in employees:
            team = employee.get('team', 'Unknown')
            if team not in teams:
                teams[team] = []
            teams[team].append(employee)

        # Filter teams with at least 3 members
        valid_teams = {team: members for team, members in teams.items() if len(members) >= 3}

        # If no valid teams, use all teams
        if not valid_teams:
            valid_teams = teams

        # Convert to list of tuples for easier random selection
        team_list = list(valid_teams.items())
        random.shuffle(team_list)

        # Store data and return initialization info
        data_id = self.game_manager.store_game_data(team_list)

        return {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': len(team_list)  # 1 point per correctly identified team
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
        if game_data is None:
            return {'game_over': True}

        # Check if we've used all teams
        if len(used_indices) >= len(game_data):
            return {'game_over': True}

        # Get the next unused index
        available_indices = [i for i in range(len(game_data)) if i not in used_indices]
        if not available_indices:
            return {'game_over': True}

        # Select a random index from available indices
        index = random.choice(available_indices)
        used_indices.append(index)

        # Get the team and its members
        team_name, team_members = game_data[index]

        # Get up to 4 team members for the question
        selected_members = team_members
        if len(selected_members) > 4:
            selected_members = random.sample(selected_members, 4)

        # Get image URLs for the selected members
        member_data = []
        for member in selected_members:
            image_url = member.get('photo', '')
            name = f"{member.get('first_name', '')} {member.get('last_name', '')}"
            member_data.append({
                'image_url': image_url,
                'name': name
            })

        # Get other random names for choices
        all_names = [f"{member.get('first_name', '')} {member.get('last_name', '')}" for member in self.game_manager.employee_data.get_all_employees()]
        correct_names = [f"{member.get('first_name', '')} {member.get('last_name', '')}" for member in selected_members]

        # Create choices for each member
        member_choices = []
        for member in selected_members:
            correct_name = f"{member.get('first_name', '')} {member.get('last_name', '')}"

            # Get random names excluding the correct names
            other_names = [name for name in all_names if name not in correct_names and name != correct_name]
            random.shuffle(other_names)

            # Create choices (1 correct + 3 incorrect)
            choices = [correct_name] + other_names[:3]
            random.shuffle(choices)

            member_choices.append({
                'image_url': member.get('photo', ''),
                'name': correct_name,
                'choices': choices
            })

        return {
            'game_over': False,
            'team_name': team_name,
            'members': member_choices,
            'current_question': current_question + 1
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.

        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        # In this mode, we count correct team identifications
        correct_answers = kwargs.get('correct_answers', 0)
        total_members = kwargs.get('total_members', 0)

        # Calculate score based on percentage of correct answers
        if total_members > 0:
            score_increment = round(correct_answers / total_members)
        else:
            score_increment = 0

        # Update the score
        stat_updates = {}
        if score_increment > 0:
            stat_updates['team'] = 1
        if correct_answers:
            stat_updates['name'] = correct_answers
        self.game_manager.score_manager.update_score(
            user_id,
            score_increment=score_increment,
            stat_updates=stat_updates if stat_updates else None,
        )

    def _parse_answer(self, form_data: dict) -> dict:
        return {
            'correct_answers': int(form_data.get('correct_answers', 0)),
            'total_members': int(form_data.get('total_members', 0)),
        }
