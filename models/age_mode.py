# models/age_mode.py
import random
from datetime import datetime
from typing import Any, ClassVar, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class AgeMode(GameMode):
    """Guess an employee's age (±5 year distractors)."""

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name', 'birth_date']
    difficulty: ClassVar[int] = 3
    estimated_duration_sec: ClassVar[int] = 120
    tags: ClassVar[List[str]] = ['culture']
    icon: ClassVar[str] = 'fa-cake-candles'
    preview_type: ClassVar[str] = 'age'

    @property
    def name(self) -> str:
        return "age"

    @property
    def display_name(self):
        return _l("Âge")

    @property
    def description(self):
        return _l("Quel âge a la personne ? Devinez l'âge de la personne affichée")

    @property
    def template(self) -> str:
        return "age.html"

    def get_question_data(self, data_id: int, used_indices: List[int],
                          current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        birth_date_str = selected.get('birth_date')
        if not birth_date_str:
            return self.get_question_data(data_id, used_indices, current_question - 1)

        try:
            birth_date = datetime.strptime(birth_date_str.split('T')[0], '%Y-%m-%d')
            current_date = datetime.now()
            age = current_date.year - birth_date.year
            if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
                age -= 1

            other_options: List[int] = []
            while len(other_options) < 3:
                option = age + random.randint(-5, 5)
                if option > 0 and option != age and option not in other_options:
                    other_options.append(option)

            choices = other_options + [age]
            random.shuffle(choices)

            return {
                'game_over': False,
                'employee': selected,
                'age': age,
                'choices': choices,
                'current_question': current_question,
                'total_questions': len(self.game_manager.get_game_data(data_id)),
            }
        except Exception as e:
            print(f"Error calculating age: {e}")
            return self.get_question_data(data_id, used_indices, current_question - 1)

    def update_score(self, user_id: int, **kwargs) -> None:
        if kwargs.get('correct_answer', 0):
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=1,
                stat_updates={'name': 1},
            )
