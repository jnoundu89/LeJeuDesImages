# models/mirror_mode.py
import random
from typing import Any, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class MirrorMode(GameMode):
    """
    Mirror game mode where players see a horizontally flipped (mirrored) image of an employee
    and need to guess who it is.
    """
    MIRROR_FACTS = [
        'Saviez-vous que notre cerveau a du mal à reconnaître les visages inversés?',
        'Les visages en miroir peuvent sembler très différents de la réalité!',
        'Notre cerveau est habitué à voir les visages dans un certain sens.',
        "L'effet miroir peut rendre méconnaissable même un visage familier!",
        "Les asymétries faciales deviennent plus évidentes quand l'image est inversée.",
    ]

    @property
    def name(self) -> str:
        return 'mirror'

    @property
    def description(self) -> str:
        return _l("Mode Miroir : identifiez la personne dont l'image est inversée horizontalement")

    @property
    def template(self) -> str:
        return 'mirror.html'

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
            'mirror_fact': random.choice(self.MIRROR_FACTS),
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
