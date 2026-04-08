# models/game_mode.py
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

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
    def description(self) -> str:
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
            'reverse_mode': False,
            'max_score': len(employees)
        }

    @abstractmethod
    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_score(self, user_id: int, **kwargs) -> None:
        pass

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
    """
    Normal game mode where users identify company, team, name, and position from an image.
    """
    @property
    def name(self) -> str:
        return "normal"

    @property
    def description(self) -> str:
        return "Identifiez l'entreprise, l'équipe, le nom et le poste de la personne sur l'image"

    @property
    def template(self) -> str:
        return "index.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        return self.game_manager.initialize_normal_mode(user_id)

    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        return self.game_manager.get_question_data(data_id, used_indices, current_question, False)

    def update_score(self, user_id: int, **kwargs) -> None:
        score_increment = kwargs.get('score_increment', 0)
        company_correct = kwargs.get('company_correct', 0)
        team_correct = kwargs.get('team_correct', 0)
        name_correct = kwargs.get('name_correct', 0)
        position_correct = kwargs.get('position_correct', 0)

        self.game_manager.update_score_normal_mode(
            user_id, score_increment, company_correct, team_correct, name_correct, position_correct
        )


class ReverseMode(GameMode):
    """
    Reverse game mode where users identify the person from a name.
    """
    @property
    def name(self) -> str:
        return "reverse"

    @property
    def description(self) -> str:
        return "Identifiez la personne correspondant au nom affiché"

    @property
    def template(self) -> str:
        return "reverse.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        return self.game_manager.initialize_reverse_mode(user_id)

    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        return self.game_manager.get_question_data(data_id, used_indices, current_question, True)

    def update_score(self, user_id: int, **kwargs) -> None:
        correct_answer = kwargs.get('correct_answer', 0)
        self.game_manager.update_score_reverse_mode(user_id, correct_answer)


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
