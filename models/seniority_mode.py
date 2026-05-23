# models/seniority_mode.py
import random
from datetime import datetime
from typing import Any, ClassVar, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class SeniorityMode(GameMode):
    """Guess how many years the employee has been with the company."""

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name', 'contract_start']
    difficulty: ClassVar[int] = 3
    estimated_duration_sec: ClassVar[int] = 120
    tags: ClassVar[List[str]] = ['culture']
    icon: ClassVar[str] = 'fa-business-time'
    preview_type: ClassVar[str] = 'static'

    @property
    def name(self) -> str:
        return "seniority"

    @property
    def display_name(self):
        return _l("Ancienneté")

    @property
    def description(self):
        return _l("Combien d'années d'ancienneté ? Devinez depuis combien d'années la personne travaille dans l'entreprise")

    @property
    def template(self) -> str:
        return "seniority.html"

    def get_question_data(self, data_id: int, used_indices: List[int],
                          current_question: int) -> Dict[str, Any]:
        selected_employee, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected_employee.get('game_over'):
            return selected_employee

        start_date_str = selected_employee.get('contract_start')
        if not start_date_str:
            return self.get_question_data(data_id, used_indices, current_question - 1)

        try:
            start_date = datetime.strptime(start_date_str.split('T')[0], '%Y-%m-%d')
            current_date = datetime.now()
            seniority_years = current_date.year - start_date.year
            if (current_date.month, current_date.day) < (start_date.month, start_date.day):
                seniority_years -= 1
            if seniority_years < 0:
                seniority_years = 0

            other_options: List[int] = []
            while len(other_options) < 3:
                option = random.randint(0, 20)
                if option != seniority_years and option not in other_options:
                    other_options.append(option)

            choices = other_options + [seniority_years]
            random.shuffle(choices)

            return {
                'game_over': False,
                'employee': selected_employee,
                'seniority_years': seniority_years,
                'choices': choices,
                'current_question': current_question,
                'total_questions': len(self.game_manager.get_game_data(data_id)),
            }
        except Exception as e:
            print(f"Error calculating seniority: {e}")
            return self.get_question_data(data_id, used_indices, current_question - 1)

    def update_score(self, user_id: int, **kwargs) -> None:
        if kwargs.get('correct_answer', 0):
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=1,
                stat_updates={'company': 1},
            )
