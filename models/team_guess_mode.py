# models/team_guess_mode.py
import random
from typing import Any, ClassVar, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class TeamGuessMode(GameMode):
    """Players see an employee and must guess which team they belong to."""

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name', 'sex', 'team', 'job_title']
    difficulty: ClassVar[int] = 2
    estimated_duration_sec: ClassVar[int] = 120
    tags: ClassVar[List[str]] = ['culture']
    icon: ClassVar[str] = 'fa-users-line'
    preview_type: ClassVar[str] = 'static'
    experimental: ClassVar[bool] = True

    @property
    def name(self) -> str:
        return "team_guess"

    @property
    def display_name(self):
        return _l("Devine l'équipe")

    @property
    def description(self):
        return _l("Mode équipe : devinez à quelle équipe appartient chaque employé")

    @property
    def template(self) -> str:
        return "team_guess.html"

    def get_question_data(self, data_id: int, used_indices: List[int],
                          current_question: int) -> Dict[str, Any]:
        selected_employee, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected_employee.get('game_over'):
            return selected_employee

        all_teams = self.game_manager.employee_data.get_unique_values('team')

        correct_team = selected_employee['team']
        if correct_team not in all_teams:
            all_teams.append(correct_team)

        if len(all_teams) > 4:
            other_teams = [team for team in all_teams if team != correct_team]
            selected_teams = random.sample(other_teams, 3)
            team_choices = selected_teams + [correct_team]
            random.shuffle(team_choices)
        else:
            team_choices = all_teams
            random.shuffle(team_choices)

        return {
            'game_over': False,
            'image_url': selected_employee['photo'],
            'name': f"{selected_employee['first_name']} {selected_employee['last_name']}",
            'position': selected_employee['job_title'],
            'correct_team': correct_team,
            'team_choices': team_choices,
            'current_question': current_question,
            'total_questions': len(self.game_manager.get_game_data(data_id)),
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        if kwargs.get('correct_answer', 0):
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=1,
                stat_updates={'team': 1},
            )
