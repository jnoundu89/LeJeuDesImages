# models/clue_mode.py
from typing import Any, Dict, List, Optional

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class ClueMode(GameMode):
    """
    Clue game mode where players receive progressive hints (initials, team, function)
    and must guess who the person is with the fewest hints possible to maximize their score.
    """
    @property
    def name(self) -> str:
        return 'clue'

    @property
    def description(self) -> str:
        return _l("Mode indices : devinez qui est la personne avec le minimum d'indices")

    @property
    def template(self) -> str:
        return 'clue.html'

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        result = super().initialize(user_id)
        # Maximum 3 points per employee (fewer hints = more points)
        result['max_score'] = (result['max_score']) * 3
        return result

    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        clues = self._generate_clues(selected)

        return {
            'game_over': False,
            'image_url': selected['photo'],
            'correct_name': self._make_full_name(selected),
            'name_choices': self._get_name_choices(selected),
            'current_question': current_question,
            'clues': clues,
        }

    def _generate_clues(self, employee: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Generate a list of clues for the employee.

        Args:
            employee: Dictionary with employee data

        Returns:
            List of clue dictionaries
        """
        clues = []

        # Clue 1: Team
        team = employee.get('team', '')
        if team:
            clues.append({
                'type': 'team',
                'text': f"Équipe : {team}",
                'level': 1,
                'points': 3
            })

        # Clue 2: Manager
        manager = employee.get('manager_name', '')
        if manager:
            clues.append({
                'type': 'manager',
                'text': f"Manager : {manager}",
                'level': 2,
                'points': 2
            })

        # Clue 3: Age (calculated from birth_date)
        birth_date = employee.get('birth_date', '')
        if birth_date:
            from datetime import datetime
            try:
                # Parse the birth_date (format: YYYY-MM-DDT00:00:00)
                birth_date = datetime.strptime(birth_date, '%Y-%m-%dT%H:%M:%S')
                # Calculate age
                today = datetime.now()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

                clues.append({
                    'type': 'age',
                    'text': f"Âge : {age} ans",
                    'level': 3,
                    'points': 1
                })
            except (ValueError, TypeError):
                # If there's an error parsing the date, skip this clue
                pass

        # Clue 4: Position
        position = employee.get('job_title', '')
        if position:
            clues.append({
                'type': 'position',
                'text': f"Poste : {position}",
                'level': 4,
                'points': 1
            })

        return clues

    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.

        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        # In this mode, score depends on how many clues were used
        correct_answer = kwargs.get('correct_answer', 0)
        clues_used = kwargs.get('clues_used', 0)

        if correct_answer:
            # Calculate score based on clues used (fewer clues = higher score)
            # Maximum 3 points if guessed with 1 clue, minimum 1 point if all clues used
            max_clues = 3  # Assuming we have 3 clues max
            score_increment = max(1, max_clues - clues_used + 1) if clues_used > 0 else max_clues

            # Update the score and name statistic
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=score_increment,
                stat_updates={'name': 1},
            )
