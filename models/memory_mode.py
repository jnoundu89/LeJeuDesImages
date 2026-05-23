# models/memory_mode.py
import random
from typing import Any, ClassVar, Dict, List, Optional

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode

PAIRS_PER_LEVEL = 8


class MemoryMode(GameMode):
    """
    Memory game mode where players must match photos with names, similar to the classic memory card game.
    """

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name']
    min_eligible_employees: ClassVar[int] = PAIRS_PER_LEVEL
    difficulty: ClassVar[int] = 1
    estimated_duration_sec: ClassVar[int] = 180
    tags: ClassVar[List[str]] = ['memoire', 'rapide', 'nouveau']
    icon: ClassVar[str] = 'fa-brain'
    preview_type: ClassVar[str] = 'memory'

    @property
    def name(self) -> str:
        return "memory"

    @property
    def display_name(self):
        return _l("Mémoire")

    @property
    def description(self):
        return _l("Mode mémoire : associez les photos avec les noms en retournant des cartes")

    @property
    def template(self) -> str:
        return "memory.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        user_id = self.game_manager.score_manager.initialize_user(user_id, mode=self.name)

        employees = self._prepare_employees()
        selected_employees = employees[:PAIRS_PER_LEVEL]
        memory_cards = self._build_cards(selected_employees)

        data_id = self.game_manager.store_game_data({
            'cards': memory_cards,
            'employees': selected_employees,
        })

        return {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': len(selected_employees),
        }

    @staticmethod
    def _build_cards(employees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cards: List[Dict[str, Any]] = []
        for employee in employees:
            full_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
            cards.append({
                'type': 'image',
                'value': employee.get('photo', ''),
                'match_id': full_name,
                'display': employee.get('photo', ''),
            })
            cards.append({
                'type': 'name',
                'value': full_name,
                'match_id': full_name,
                'display': full_name,
            })
        random.shuffle(cards)
        return cards

    def get_question_data(self, data_id: int, used_indices: List[int],
                          current_question: int) -> Dict[str, Any]:
        game_data = self.game_manager.get_game_data(data_id)
        if game_data is None:
            return {'game_over': True}

        if current_question == 0:
            return {
                'game_over': False,
                'cards': game_data['cards'],
                'current_question': 1,
                'total_pairs': len(game_data['employees']),
            }

        matched_pairs = int(len(used_indices))
        if matched_pairs >= len(game_data['employees']) and matched_pairs > 0:
            new_employees = self._next_level_employees(game_data['employees'])
            memory_cards = self._build_cards(new_employees)
            game_data['cards'] = memory_cards
            game_data['employees'] = new_employees
            self.game_manager.update_game_data(data_id, game_data)

            return {
                'game_over': False,
                'cards': memory_cards,
                'current_question': current_question + 1,
                'total_pairs': len(new_employees),
            }

        if len(used_indices) >= len(game_data['employees']):
            return {'game_over': True}

        return {
            'game_over': False,
            'cards': game_data['cards'],
            'current_question': current_question,
            'total_pairs': len(game_data['employees']),
        }

    def _next_level_employees(
        self, previous_employees: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        employees = self._prepare_employees()
        new_employees: List[Dict[str, Any]] = []

        for employee in employees:
            if len(new_employees) >= PAIRS_PER_LEVEL:
                break
            was_in_previous = any(
                (employee.get('first_name') == prev.get('first_name')
                 and employee.get('last_name') == prev.get('last_name'))
                for prev in previous_employees
            )
            if not was_in_previous:
                new_employees.append(employee)

        if len(new_employees) < PAIRS_PER_LEVEL:
            random.shuffle(employees)
            for employee in employees:
                if len(new_employees) >= PAIRS_PER_LEVEL:
                    break
                if employee not in new_employees:
                    new_employees.append(employee)

        return new_employees

    def update_score(self, user_id: int, **kwargs) -> None:
        matched_pairs = kwargs.get('matched_pairs', 0)
        self.game_manager.score_manager.update_score(
            user_id,
            score_increment=matched_pairs,
            stat_updates={'name': matched_pairs},
        )

    def _parse_answer(self, form_data: dict) -> dict:
        return {'matched_pairs': int(form_data.get('matched_pairs', 0))}

    def _session_updates_for(self, payload: dict, session_data: dict) -> dict:
        matched = payload.get('matched_pairs', 0)
        if matched > 0:
            return {'used_indices': list(range(matched))}
        return {}
