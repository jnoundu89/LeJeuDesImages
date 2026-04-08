# models/speed_mode.py
from typing import Any, Dict, List, Optional

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class SpeedMode(GameMode):
    """
    Speed game mode where players have a limited time to identify as many employees as possible.
    The faster they answer, the more points they earn.
    """
    @property
    def name(self) -> str:
        return 'speed'

    @property
    def description(self) -> str:
        return _l("Mode vitesse : identifiez un maximum d'employés en un temps limité, plus vous êtes rapide, plus vous gagnez de points")

    @property
    def template(self) -> str:
        return 'speed.html'

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        result = super().initialize(user_id)
        result['max_score'] = result['max_score'] * 3  # Max 3 pts per employee
        result['time_limit'] = 60
        return result

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
