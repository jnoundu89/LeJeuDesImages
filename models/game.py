# models/game.py
from typing import Any, Dict
from uuid import uuid4

from .employee import EmployeeData
from .score import ScoreManager


class GameManager:
    """
    Class to handle game logic for different game modes.
    """
    def __init__(self, employee_data: EmployeeData, score_manager: ScoreManager):
        """
        Initialize the game manager.

        Args:
            employee_data: EmployeeData instance for accessing employee data
            score_manager: ScoreManager instance for managing scores
        """
        self.employee_data = employee_data
        self.score_manager = score_manager
        self.game_data_cache = {}

    def store_game_data(self, data: Any) -> int:
        """
        Store game data in the cache and return a unique ID.

        Args:
            data: List of employee dictionaries to store

        Returns:
            Unique ID for the stored data
        """
        data_id = uuid4().int % 10**9
        self.game_data_cache[data_id] = data
        return data_id

    def get_game_data(self, data_id: int) -> Any:
        """
        Get game data from the cache.

        Args:
            data_id: ID of the data to retrieve

        Returns:
            List of employee dictionaries
        """
        return self.game_data_cache.get(data_id, [])

    def update_game_data(self, data_id: int, data: Any) -> None:
        """
        Update game data in the cache.

        Args:
            data_id: ID of the data to update
            data: New data to store
        """
        if data_id in self.game_data_cache:
            self.game_data_cache[data_id] = data

    def get_result_data(self, user_id: int, max_score: int, total_questions: int) -> Dict[str, Any]:
        """
        Get data for the result page.

        Args:
            user_id: The user ID
            max_score: The maximum possible score
            total_questions: The total number of questions answered

        Returns:
            Dictionary with result data
        """
        user_score = self.score_manager.get_user_score(user_id)
        stats = self.score_manager.get_stats(user_id)

        return {
            'score': user_score['score'],
            'max_score': max_score,
            'current_score': user_score['score'],
            'total_questions': total_questions,
            'stats': stats
        }
