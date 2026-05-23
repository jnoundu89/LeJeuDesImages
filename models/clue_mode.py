# models/clue_mode.py
from typing import Any, ClassVar, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class ClueMode(GameMode):
    """
    Clue game mode where players receive progressive hints (initials, team, function)
    and must guess who the person is with the fewest hints possible to maximize their score.
    """

    required_fields: ClassVar[List[str]] = [
        'photo', 'first_name', 'last_name', 'sex', 'team', 'job_title',
    ]
    difficulty: ClassVar[int] = 2
    estimated_duration_sec: ClassVar[int] = 180
    tags: ClassVar[List[str]] = ['devinette', 'culture']
    icon: ClassVar[str] = 'fa-magnifying-glass'
    preview_type: ClassVar[str] = 'clue'
    score_multiplier: ClassVar[int] = 3

    @property
    def name(self) -> str:
        return 'clue'

    @property
    def display_name(self):
        return _l("Indices")

    @property
    def description(self):
        return _l("Mode indices : devinez qui est la personne avec le minimum d'indices")

    @property
    def template(self) -> str:
        return 'clue.html'

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
            'clues': self._generate_clues(selected),
        }

    def _generate_clues(self, employee: Dict[str, str]) -> List[Dict[str, str]]:
        clues = []

        team = employee.get('team', '')
        if team:
            clues.append({'type': 'team', 'text': f"Équipe : {team}", 'level': 1, 'points': 3})

        manager = employee.get('manager_name', '')
        if manager:
            clues.append({'type': 'manager', 'text': f"Manager : {manager}", 'level': 2, 'points': 2})

        birth_date = employee.get('birth_date', '')
        if birth_date:
            from datetime import datetime
            try:
                birth_date_dt = datetime.strptime(birth_date, '%Y-%m-%dT%H:%M:%S')
                today = datetime.now()
                age = today.year - birth_date_dt.year - (
                    (today.month, today.day) < (birth_date_dt.month, birth_date_dt.day)
                )
                clues.append({'type': 'age', 'text': f"Âge : {age} ans", 'level': 3, 'points': 1})
            except (ValueError, TypeError):
                pass

        position = employee.get('job_title', '')
        if position:
            clues.append({'type': 'position', 'text': f"Poste : {position}", 'level': 4, 'points': 1})

        return clues

    def update_score(self, user_id: int, **kwargs) -> None:
        correct_answer = kwargs.get('correct_answer', 0)
        clues_used = kwargs.get('clues_used', 0)

        if correct_answer:
            max_clues = 3
            score_increment = max(1, max_clues - clues_used + 1) if clues_used > 0 else max_clues
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=score_increment,
                stat_updates={'name': 1},
            )

    def _parse_answer(self, form_data: dict) -> dict:
        return {
            'correct_answer': int(form_data.get('correct_answer', 0)),
            'clues_used': int(form_data.get('clues_used', 0)),
        }
