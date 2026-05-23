# models/pixelation_mode.py
from typing import Any, ClassVar, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class PixelationMode(GameMode):
    """
    Pixelation game mode where an image starts extremely pixelated and gradually becomes clearer.
    Players need to identify the person's name from 4 options.
    """

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name', 'sex']
    difficulty: ClassVar[int] = 2
    estimated_duration_sec: ClassVar[int] = 120
    tags: ClassVar[List[str]] = ['photo', 'devinette', 'populaire']
    icon: ClassVar[str] = 'fa-puzzle-piece'
    preview_type: ClassVar[str] = 'pixelation'

    @property
    def name(self) -> str:
        return 'pixelation'

    @property
    def display_name(self):
        return _l("Pixélisation")

    @property
    def description(self):
        return _l("Mode pixelisation : identifiez la personne sur l'image qui devient progressivement plus nette")

    @property
    def template(self) -> str:
        return 'pixelation.html'

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
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        correct_answer = kwargs.get('correct_answer', 0)
        if correct_answer:
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=1,
                stat_updates={'name': 1},
            )
