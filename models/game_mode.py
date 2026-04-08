# models/game_mode.py
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

from flask_babel import lazy_gettext as _l

from .game import GameManager


class GameMode(ABC):
    """
    Abstract base class for game modes.
    """
    def __init__(self, game_manager: GameManager):
        self.game_manager = game_manager

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> Union[str, Any]:  # LazyString from flask_babel
        pass

    @property
    @abstractmethod
    def template(self) -> str:
        pass

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Default initialize: init user, get all employees, shuffle, store, return dict."""
        user_id = self.game_manager.score_manager.initialize_user(user_id)
        employees = self.game_manager.employee_data.get_all_employees()
        random.shuffle(employees)
        data_id = self.game_manager.store_game_data(employees)
        return {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': len(employees)
        }

    @abstractmethod
    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_score(self, user_id: int, **kwargs) -> None:
        pass

    def handle_answer(self, user_id: int, form_data: dict, session_data: dict) -> dict:
        """Parse submitted form, update score, return session changes.

        Default: reads ``correct_answer`` from form and delegates to
        ``update_score``.  Override in modes that need different form
        fields or session mutations (e.g. NormalMode, MemoryMode).

        Returns a dict of session keys to update (empty by default).
        """
        correct_answer = int(form_data.get('correct_answer', 0))
        self.update_score(user_id, correct_answer=correct_answer)
        return {}

    # ------------------------------------------------------------------
    # Protected helpers – shared boilerplate for simple modes
    # ------------------------------------------------------------------

    def _pick_next_employee(
        self,
        data_id: int,
        used_indices: List[int],
        current_question: int,
    ) -> Tuple[Dict[str, Any], int]:
        """Pick the next employee sequentially.

        Returns:
            (selected_employee, current_question) or
            ({'game_over': True}, current_question) when done.
        """
        game_data = self.game_manager.get_game_data(data_id)

        if len(used_indices) >= len(game_data):
            return {'game_over': True}, current_question

        available_indices = [i for i in range(len(game_data)) if i not in used_indices]
        if not available_indices:
            return {'game_over': True}, current_question

        index = available_indices[0]
        used_indices.append(index)
        current_question += 1

        return game_data[index], current_question

    def _get_name_choices(
        self,
        selected_employee: Dict[str, Any],
        all_employees: Optional[List[Dict[str, Any]]] = None,
        count: int = 4,
    ) -> List[str]:
        """Return *count* full-name strings (1 correct + count-1 distractors) filtered by sex."""
        full_name = self._make_full_name(selected_employee)

        filtered_employees = self.game_manager.employee_data.get_filtered_employees(
            {'sex': selected_employee['sex']}
        )
        other_employees = [
            e for e in filtered_employees
            if e['first_name'] != selected_employee['first_name']
            or e['last_name'] != selected_employee['last_name']
        ]

        needed = count - 1
        if len(other_employees) >= needed:
            other_employees = random.sample(other_employees, needed)

        names = [full_name] + [self._make_full_name(e) for e in other_employees]
        random.shuffle(names)
        return names

    @staticmethod
    def _make_full_name(employee: Dict[str, Any]) -> str:
        return f"{employee['first_name']} {employee['last_name']}"


class NormalMode(GameMode):
    """Normal game mode: identify company, team, name, and position from an image."""

    @property
    def name(self) -> str:
        return 'normal'

    @property
    def description(self) -> str:
        return _l("Identifiez l'entreprise, l'équipe, le nom et le poste de la personne sur l'image")

    @property
    def template(self) -> str:
        return 'normal.html'

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        user_id = self.game_manager.score_manager.initialize_user(user_id)
        employees = self.game_manager.employee_data.get_all_employees()
        random.shuffle(employees)
        data_id = self.game_manager.store_game_data(employees)
        return {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': len(employees) * 4,
        }

    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        correct_values = {
            'company': selected['company'],
            'team': selected['team'],
            'name': self._make_full_name(selected),
            'position': selected['job_title'],
        }

        companies = self.game_manager.employee_data.get_unique_values('company')
        teams = self.game_manager.employee_data.get_random_choices('team', correct_values['team'])
        names = self._get_name_choices(selected)
        sex_filter = {'sex': selected['sex']}
        positions = self.game_manager.employee_data.get_random_choices(
            'job_title', correct_values['position'], filter_dict=sex_filter
        )

        return {
            'game_over': False,
            'image_url': selected['photo'],
            'correct_values': correct_values,
            'choices': {
                'companies': companies,
                'teams': teams,
                'names': names,
                'positions': positions,
            },
            'current_question': current_question,
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        score_increment = kwargs.get('score_increment', 0)
        stat_updates = {}
        for key in ('company', 'team', 'name', 'position'):
            val = kwargs.get(f'{key}_correct', 0)
            if val:
                stat_updates[key] = val
        self.game_manager.score_manager.update_score(user_id, score_increment, stat_updates=stat_updates)

    def handle_answer(self, user_id: int, form_data: dict, session_data: dict) -> dict:
        self.update_score(
            user_id,
            score_increment=int(form_data.get('score_increment', 0)),
            company_correct=int(form_data.get('company_correct', 0)),
            team_correct=int(form_data.get('team_correct', 0)),
            name_correct=int(form_data.get('name_correct', 0)),
            position_correct=int(form_data.get('position_correct', 0)),
        )
        return {}


class ReverseMode(GameMode):
    """Reverse game mode: identify the person from a name."""

    @property
    def name(self) -> str:
        return 'reverse'

    @property
    def description(self) -> str:
        return _l("Identifiez la personne correspondant au nom affiché")

    @property
    def template(self) -> str:
        return 'reverse.html'

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        user_id = self.game_manager.score_manager.initialize_user(user_id)
        employees = self.game_manager.employee_data.get_all_employees()
        random.shuffle(employees)
        data_id = self.game_manager.store_game_data(employees)
        return {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': len(employees),
        }

    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        correct_value = self._make_full_name(selected)
        sex_filter = {'sex': selected['sex']}
        filtered = self.game_manager.employee_data.get_filtered_employees(sex_filter)
        others = [e for e in filtered if self._make_full_name(e) != correct_value]
        if len(others) > 3:
            others = random.sample(others, 3)

        choices = [selected] + others
        random.shuffle(choices)

        return {
            'game_over': False,
            'correct_value': correct_value,
            'choices': choices,
            'current_question': current_question,
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        if kwargs.get('correct_answer', 0):
            self.game_manager.score_manager.update_score(user_id, 1, stat_updates={'name': 1})
        else:
            self.game_manager.score_manager.update_score(user_id, 0)


class GameModeFactory:
    """
    Factory class for creating and managing game modes.
    """
    def __init__(self, game_manager: GameManager):
        """
        Initialize the game mode factory.

        Args:
            game_manager: GameManager instance for managing the game
        """
        self.game_manager = game_manager
        self.modes = {}

        # Register default game modes
        self.register_mode(NormalMode(game_manager))
        self.register_mode(ReverseMode(game_manager))

    def register_mode(self, mode: GameMode) -> None:
        """
        Register a new game mode.

        Args:
            mode: GameMode instance to register
        """
        self.modes[mode.name] = mode

    def get_mode(self, mode_name: str) -> Optional[GameMode]:
        """
        Get a game mode by name.

        Args:
            mode_name: Name of the game mode

        Returns:
            GameMode instance or None if not found
        """
        return self.modes.get(mode_name)

    def get_all_modes(self) -> Dict[str, GameMode]:
        """
        Get all registered game modes.

        Returns:
            Dictionary of game mode names to GameMode instances
        """
        return self.modes
