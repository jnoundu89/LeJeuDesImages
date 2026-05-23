# models/zoom_mode.py
import random
from typing import Any, ClassVar, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class ZoomMode(GameMode):
    """
    Zoom game mode where players identify an employee as their photo
    progressively zooms out over time.
    """

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name', 'sex']
    difficulty: ClassVar[int] = 2
    estimated_duration_sec: ClassVar[int] = 120
    tags: ClassVar[List[str]] = ['visuel']
    icon: ClassVar[str] = 'fa-magnifying-glass-minus'
    preview_type: ClassVar[str] = 'zoom'
    score_multiplier: ClassVar[int] = 3

    @property
    def name(self) -> str:
        return 'zoom'

    @property
    def display_name(self):
        return _l("Zoom")

    @property
    def description(self):
        return _l("Mode Zoom : Identifiez l'employé alors que sa photo dézoome au fil des secondes")

    @property
    def template(self) -> str:
        return 'zoom.html'

    def get_question_data(self, data_id: int, used_indices: List[int],
                          current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        # Generate choices
        sex_filter = {'sex': selected['sex']}
        other_employees = self.game_manager.employee_data.get_filtered_employees(sex_filter)
        other_employees = [e for e in other_employees if e != selected]

        # Robustness fallback
        if len(other_employees) < 3:
            all_other = self.game_manager.employee_data.get_all_employees()
            other_employees = [e for e in all_other if e != selected]

        if len(other_employees) > 3:
            choices = random.sample(other_employees, 3)
        else:
            choices = other_employees

        choices.append(selected)
        random.shuffle(choices)

        choices_names = [f"{c.get('first_name', '')} {c.get('last_name', '')}" for c in choices]
        correct_name = f"{selected.get('first_name', '')} {selected.get('last_name', '')}"

        game_data = self.game_manager.get_game_data(data_id)

        return {
            'game_over': False,
            'employee': selected,
            'image_url': selected['photo'],
            'correct_name': correct_name,
            'name_choices': choices_names,
            'current_question': current_question,
            'total_questions': len(game_data),
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        correct_answer = kwargs.get('correct_answer', 0)
        remaining_sec = kwargs.get('remaining_sec', 0)

        if correct_answer:
            # Reward early answer based on remaining seconds (timer is 30s)
            if remaining_sec > 20:
                score_increment = 3
            elif remaining_sec > 10:
                score_increment = 2
            else:
                score_increment = 1

            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=score_increment,
                stat_updates={'name': 1}
            )

    def _parse_answer(self, form_data: dict) -> dict:
        return {
            'correct_answer': int(form_data.get('correct_answer', 0)),
            'remaining_sec': float(form_data.get('remaining_sec', 0)),
        }
