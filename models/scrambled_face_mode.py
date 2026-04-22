# models/scrambled_face_mode.py
import random
from typing import Any, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class ScrambledFaceMode(GameMode):
    """
    Scrambled Face game mode where parts of faces are mixed up and players need to identify the person.
    The image is divided into sections (eyes, nose, mouth) and scrambled with parts from other employees.
    """
    @property
    def name(self) -> str:
        return 'scrambled_face'

    @property
    def description(self) -> str:
        return _l("Mode Visage Mélangé : identifiez la personne dont le visage a été mélangé avec d'autres")

    @property
    def template(self) -> str:
        return 'scrambled_face.html'

    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        full_name = self._make_full_name(selected)

        # Scramble logic: pick 3 random other employees for face parts
        all_employees = self.game_manager.employee_data.get_all_employees()
        others_for_scramble = [
            e for e in all_employees
            if e['first_name'] != selected['first_name'] or e['last_name'] != selected['last_name']
        ]
        random_employees = random.sample(others_for_scramble, min(3, len(others_for_scramble)))

        scrambled_data = {
            'main_image': selected['photo'],
            'scramble_images': [emp['photo'] for emp in random_employees],
        }

        return {
            'game_over': False,
            'image_url': selected['photo'],
            'scrambled_data': scrambled_data,
            'correct_name': full_name,
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
