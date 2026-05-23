# models/example_mode.py
from typing import Any, ClassVar, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class ExampleMode(GameMode):
    """
    Example game mode to demonstrate how to add a new game mode.
    This mode is a simplified version of the normal mode where users only need to identify the name.
    """

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name', 'sex']
    difficulty: ClassVar[int] = 1
    estimated_duration_sec: ClassVar[int] = 60
    tags: ClassVar[List[str]] = []
    icon: ClassVar[str] = 'fa-circle-play'
    preview_type: ClassVar[str] = 'static'
    experimental: ClassVar[bool] = True

    @property
    def name(self) -> str:
        return "example"

    @property
    def display_name(self):
        return _l("Exemple")

    @property
    def description(self):
        return _l("Mode exemple : identifiez uniquement le nom de la personne sur l'image")

    @property
    def template(self) -> str:
        return "example.html"

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
        if kwargs.get('correct_answer', 0):
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=1,
                stat_updates={'name': 1},
            )
