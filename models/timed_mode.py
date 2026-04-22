# models/timed_mode.py
from typing import Any, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class TimedMode(GameMode):
    """
    Timed game mode where players must identify the maximum number of people in a limited time (2 minutes).
    The final score depends on the number of people correctly identified.
    """
    @property
    def name(self) -> str:
        return 'timed'

    @property
    def display_name(self):
        return _l("Chronométré")

    @property
    def description(self):
        return _l("Mode chronométré : identifiez le maximum de personnes en 2 minutes")

    @property
    def template(self) -> str:
        return 'timed.html'

    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        return {
            'game_over': False,
            'image_url': selected['photo'],
            'correct_name': self._make_full_name(selected),
            'name_choices': self._get_name_choices(selected),
            'current_question': current_question,
            'total_time': 120,
            'correct_values': selected,
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        correct_answer = kwargs.get('correct_answer', 0)
        if correct_answer:
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=1,
                stat_updates={'name': 1},
            )
