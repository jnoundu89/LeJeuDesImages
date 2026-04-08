# models/progressive_hint_mode.py
import random
from typing import Any, Dict, List, Optional

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class ProgressiveHintMode(GameMode):
    """
    Progressive Hint game mode where players get progressive hints about an employee
    and need to identify them as early as possible for more points.
    """
    @property
    def name(self) -> str:
        return 'progressive_hint'

    @property
    def description(self) -> str:
        return _l("Mode indices progressifs : identifiez l'employé avec le moins d'indices possible pour gagner plus de points")

    @property
    def template(self) -> str:
        return 'progressive_hint.html'

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        result = super().initialize(user_id)
        result['max_score'] = result['max_score'] * 3
        return result

    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        hints = [
            {
                'level': 1,
                'text': f"Cette personne travaille chez {selected['company']}",
                'points': 3,
            },
            {
                'level': 2,
                'text': f"Cette personne fait partie de l'équipe {selected['team']}",
                'points': 2,
            },
            {
                'level': 3,
                'text': f"Cette personne occupe le poste de {selected['job_title']}",
                'points': 1,
            },
        ]

        # Choices are full employee dicts (not just names) for this mode
        sex_filter = {'sex': selected['sex']}
        other_employees = self.game_manager.employee_data.get_filtered_employees(sex_filter)
        other_employees = [e for e in other_employees if e != selected]

        if len(other_employees) > 3:
            choices = random.sample(other_employees, 3)
        else:
            choices = other_employees

        choices.append(selected)
        random.shuffle(choices)

        game_data = self.game_manager.get_game_data(data_id)

        return {
            'game_over': False,
            'employee': selected,
            'hints': hints,
            'choices': choices,
            'current_question': current_question,
            'total_questions': len(game_data),
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.

        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        correct_answer = kwargs.get('correct_answer', 0)
        hint_level = kwargs.get('hint_level', 3)  # Default to the maximum hint level (minimum points)

        if correct_answer:
            # Calculate points based on hint level
            # Fewer hints = more points
            if hint_level == 1:
                score_increment = 3
            elif hint_level == 2:
                score_increment = 2
            else:
                score_increment = 1

            # Update the score
            stat_updates = {'name': 1}
            if hint_level >= 1:
                stat_updates['company'] = 1
            if hint_level >= 2:
                stat_updates['team'] = 1
            if hint_level >= 3:
                stat_updates['position'] = 1
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=score_increment,
                stat_updates=stat_updates,
            )
