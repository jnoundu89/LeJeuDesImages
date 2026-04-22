# models/silhouette_mode.py
import random
from typing import Any, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class SilhouetteMode(GameMode):
    """
    Silhouette game mode where players see only the silhouette of an employee and need to guess who it is.
    """
    @property
    def name(self) -> str:
        return 'silhouette'

    @property
    def description(self) -> str:
        return _l("Mode Silhouette : identifiez la personne à partir de sa silhouette")

    @property
    def template(self) -> str:
        return 'silhouette.html'

    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        # Hint logic specific to silhouette mode
        hint_type = random.choice(['team', 'position'])
        hint = selected['team'] if hint_type == 'team' else selected['job_title']

        return {
            'game_over': False,
            'image_url': selected['photo'],
            'correct_name': self._make_full_name(selected),
            'name_choices': self._get_name_choices(selected),
            'hint_type': hint_type.capitalize(),
            'hint': hint,
            'current_question': current_question,
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        correct_answer = kwargs.get('correct_answer', 0)
        if correct_answer:
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=1,
                stat_updates={'name': 1},
            )
