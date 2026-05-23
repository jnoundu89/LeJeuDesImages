# models/manager_mode.py
import random
from typing import Any, ClassVar, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class ManagerMode(GameMode):
    """Identify the manager of a displayed employee among four portraits."""

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name', 'manager_name']
    difficulty: ClassVar[int] = 2
    estimated_duration_sec: ClassVar[int] = 150
    tags: ClassVar[List[str]] = ['culture', 'photo']
    icon: ClassVar[str] = 'fa-sitemap'
    preview_type: ClassVar[str] = 'static'

    @property
    def name(self) -> str:
        return "manager"

    @property
    def display_name(self):
        return _l("Manager")

    @property
    def description(self):
        return _l("Qui est le manager de qui ? Identifiez le manager de la personne affichée")

    @property
    def template(self) -> str:
        return "manager.html"

    def get_question_data(self, data_id: int, used_indices: List[int],
                          current_question: int) -> Dict[str, Any]:
        selected_employee, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected_employee.get('game_over'):
            return selected_employee

        manager_name = selected_employee.get('manager_name', '')

        all_employees = self.game_manager.employee_data.get_all_employees()
        manager = next(
            (emp for emp in all_employees if emp.full_name == manager_name),
            None,
        )

        if not manager:
            return self.get_question_data(data_id, used_indices, current_question - 1)

        other_employees = [
            emp for emp in all_employees
            if emp.full_name != manager_name and emp != selected_employee
        ]

        if len(other_employees) >= 3:
            choices = random.sample(other_employees, 3)
        else:
            choices = list(other_employees)

        choices.append(manager)
        random.shuffle(choices)

        return {
            'game_over': False,
            'employee': selected_employee,
            'manager': manager,
            'choices': choices,
            'current_question': current_question,
            'total_questions': len(self.game_manager.get_game_data(data_id)),
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        if kwargs.get('correct_answer', 0):
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=1,
                stat_updates={'team': 1, 'position': 1},
            )
