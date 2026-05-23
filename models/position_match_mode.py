# models/position_match_mode.py
import random
from typing import Any, ClassVar, Dict, List, Optional

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class PositionMatchMode(GameMode):
    """
    Position Match game mode where players need to match employees with their correct positions.

    The round layout is controlled by two class-level settings:
    ``employees_per_round`` and ``total_rounds``. They default to 5 and 3
    (→ 15 employees, the historical constant), but subclasses or config
    tweaks can lower them for small datasets. ``min_eligible_employees``
    is derived from their product so the availability gate stays in
    sync automatically.
    """

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name', 'job_title']
    difficulty: ClassVar[int] = 2
    estimated_duration_sec: ClassVar[int] = 180
    tags: ClassVar[List[str]] = ['culture']
    icon: ClassVar[str] = 'fa-list-check'
    preview_type: ClassVar[str] = 'static'
    experimental: ClassVar[bool] = True

    # Round layout — derived min_eligible below.
    employees_per_round: ClassVar[int] = 5
    total_rounds: ClassVar[int] = 3
    min_eligible_employees: ClassVar[int] = employees_per_round * total_rounds

    @property
    def name(self) -> str:
        return "position_match"

    @property
    def display_name(self):
        return _l("Association de postes")

    @property
    def description(self):
        return _l("Mode poste : associez chaque employé avec son poste correct")

    @property
    def template(self) -> str:
        return "position_match.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        user_id = self.game_manager.score_manager.initialize_user(user_id, mode=self.name)

        # Get eligible employees (with required fields populated)
        all_employees = self.game_manager.employee_data.get_all_employees()
        employees = self.eligible_employees(all_employees)
        random.shuffle(employees)

        # Clamp total_rounds to what the dataset can actually support so
        # small datasets don't run out of employees mid-game.
        effective_rounds = max(1, min(self.total_rounds, len(employees) // self.employees_per_round))
        effective_rounds = effective_rounds or 1  # at minimum 1

        selected_employees = employees[:self.employees_per_round]

        data_id = self.game_manager.store_game_data({
            'all_employees': employees,
            'current_round_employees': selected_employees,
            'current_round': 1,
            'total_rounds': effective_rounds,
            'employees_per_round': self.employees_per_round,
        })

        return {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': effective_rounds * self.employees_per_round,
        }

    def get_question_data(self, data_id: int, used_indices: List[int],
                          current_question: int) -> Dict[str, Any]:
        game_data = self.game_manager.get_game_data(data_id)

        current_round = game_data.get('current_round', 1)
        total_rounds = game_data.get('total_rounds', self.total_rounds)
        per_round = game_data.get('employees_per_round', self.employees_per_round)

        if current_round > total_rounds:
            return {'game_over': True}

        all_employees = game_data.get('all_employees', [])
        current_round_employees = game_data.get('current_round_employees', [])

        # If this is a new round, select new employees
        if len(used_indices) % per_round == 0 and len(used_indices) > 0:
            current_round += 1
            game_data['current_round'] = current_round

            if current_round > total_rounds:
                return {'game_over': True}

            start_index = (current_round - 1) * per_round
            end_index = start_index + per_round

            if end_index > len(all_employees):
                return {'game_over': True}

            current_round_employees = all_employees[start_index:end_index]
            game_data['current_round_employees'] = current_round_employees

        positions = [employee['job_title'] for employee in current_round_employees]
        shuffled_positions = positions.copy()
        random.shuffle(shuffled_positions)

        employees_with_positions = []
        for employee in current_round_employees:
            employees_with_positions.append({
                'employee': employee,
                'correct_position': employee['job_title'],
                'position_options': shuffled_positions,
            })

        return {
            'game_over': False,
            'employees': employees_with_positions,
            'current_round': current_round,
            'total_rounds': total_rounds,
            'current_question': current_question,
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        correct_matches = kwargs.get('correct_matches', 0)

        if correct_matches > 0:
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=correct_matches,
                stat_updates={'position': correct_matches},
            )

    def _parse_answer(self, form_data: dict) -> dict:
        return {'correct_matches': int(form_data.get('correct_matches', 0))}
