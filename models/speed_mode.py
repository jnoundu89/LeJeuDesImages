# models/speed_mode.py
from typing import Any, ClassVar, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class SpeedMode(GameMode):
    """
    Speed game mode where players have a limited time to identify as many employees as possible.
    The faster they answer, the more points they earn.
    """

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name', 'sex']
    difficulty: ClassVar[int] = 3
    estimated_duration_sec: ClassVar[int] = 60
    tags: ClassVar[List[str]] = ['rapide', 'temps']
    icon: ClassVar[str] = 'fa-gauge-high'
    preview_type: ClassVar[str] = 'static'
    score_multiplier: ClassVar[int] = 3
    experimental: ClassVar[bool] = True

    @property
    def name(self) -> str:
        return 'speed'

    @property
    def display_name(self):
        return _l("Vitesse")

    @property
    def description(self):
        return _l("Mode vitesse : identifiez un maximum d'employés en un temps limité, plus vous êtes rapide, plus vous gagnez de points")

    @property
    def template(self) -> str:
        return 'speed.html'

    def _extra_init_data(self, employees: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {'time_limit': 60}

    def get_question_data(self, data_id: int, used_indices: List[int],
                          current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        game_data = self.game_manager.get_game_data(data_id)

        return {
            'game_over': False,
            'image_url': selected['photo'],
            'correct_name': self._make_full_name(selected),
            'name_choices': self._get_name_choices(selected),
            'current_question': current_question,
            'total_questions': len(game_data),
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        correct_answer = kwargs.get('correct_answer', 0)
        response_time = kwargs.get('response_time', 0)

        if correct_answer:
            if response_time < 1000:
                score_increment = 3
            elif response_time < 3000:
                score_increment = 2
            else:
                score_increment = 1

            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=score_increment,
                stat_updates={'name': 1},
            )

    def _parse_answer(self, form_data: dict) -> dict:
        return {
            'correct_answer': int(form_data.get('correct_answer', 0)),
            'response_time': int(form_data.get('response_time', 0)),
        }
