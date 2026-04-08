# models/score.py
import logging
from typing import Any, Dict, Optional
from uuid import uuid4

from tinydb import Query, TinyDB


class ScoreManager:
    """
    Class to handle user score operations.
    """
    def __init__(self, db_path: str):
        """
        Initialize the score manager with a database path.

        Args:
            db_path: Path to the TinyDB database file
        """
        self.db = TinyDB(db_path)
        self.scores_table = self.db.table('user_scores')
        self.User = Query()

    def initialize_user(self, user_id: Optional[int] = None, mode: Optional[str] = None,
                        player_name: Optional[str] = None) -> int:
        """
        Initialize a new user or get an existing user.

        Args:
            user_id: Optional user ID. If not provided, a new user will be created.
            mode: Optional game mode identifier stored alongside the score record.
            player_name: Optional display name for the player.

        Returns:
            The user ID
        """
        if user_id is None:
            user_id = uuid4().int % 10**9

        # Check if user exists
        user_score = self.scores_table.get(self.User.user_id == user_id)

        if user_score is None:
            # Create new user
            record: Dict[str, Any] = {
                'user_id': user_id,
                'mode': mode,
                'score': 0,
                'stats': {},
                'total_correct_answers': 0,
            }
            if player_name is not None:
                record['player_name'] = player_name
            self.scores_table.insert(record)
            logging.info(f"New user created: {user_id}")

        return user_id

    def get_user_score(self, user_id: int) -> Dict[str, Any]:
        """
        Get the score data for a user.

        Args:
            user_id: The user ID

        Returns:
            Dictionary containing the user's score data
        """
        user_score = self.scores_table.get(self.User.user_id == user_id)

        if user_score is None:
            # If user doesn't exist, initialize them
            self.initialize_user(user_id)
            user_score = self.scores_table.get(self.User.user_id == user_id)

        return user_score

    def update_score(self, user_id: int, score_increment: int,
                    stat_updates: Optional[Dict[str, int]] = None) -> None:
        """
        Update a user's score.

        Args:
            user_id: The user ID
            score_increment: The amount to increment the score by
            stat_updates: Optional dict of stat keys to increment values,
                          e.g. {'name': 1, 'company': 1}
        """
        user_score = self.get_user_score(user_id)

        user_score['score'] += score_increment
        user_score['total_correct_answers'] += score_increment

        # Track best score
        if user_score['score'] > user_score.get('best_score', 0):
            user_score['best_score'] = user_score['score']

        if stat_updates:
            stats = user_score.get('stats', {})
            for key, value in stat_updates.items():
                stats[key] = stats.get(key, 0) + value
            user_score['stats'] = stats

        self.scores_table.update(user_score, self.User.user_id == user_id)
        logging.info(f"Score updated for user {user_id}: {user_score['score']}")

    def get_stats(self, user_id: int) -> Dict[str, int]:
        """
        Get the statistics for a user.

        Args:
            user_id: The user ID

        Returns:
            Dictionary containing the user's statistics
        """
        user_score = self.get_user_score(user_id)

        # Support both new flexible 'stats' dict and legacy flat fields
        stats = user_score.get('stats')
        if isinstance(stats, dict):
            return stats

        # Backwards compatibility: read legacy flat fields
        return {
            'company': user_score.get('stats_company', 0),
            'team': user_score.get('stats_team', 0),
            'name': user_score.get('stats_name', 0),
            'position': user_score.get('stats_position', 0),
        }

    def get_top_scores(self, mode: Optional[str] = None, limit: int = 10) -> list:
        """
        Get the top scores, optionally filtered by game mode.

        Args:
            mode: The game mode to filter by. When None, return all scores.
            limit: Maximum number of scores to return

        Returns:
            List of dictionaries containing the top scores
        """
        if mode is not None:
            scores = self.scores_table.search(self.User.mode == mode)
        else:
            scores = self.scores_table.all()

        sorted_scores = sorted(scores, key=lambda x: x.get('score', 0), reverse=True)
        return sorted_scores[:limit]

    def get_total_players(self) -> int:
        """
        Get the total number of players.

        Returns:
            Total number of players
        """
        return len(self.scores_table.all())

    def get_total_games(self) -> int:
        """
        Get the total number of games played.

        Returns:
            Total number of games played
        """
        # For now, we'll estimate this based on the total correct answers
        all_scores = self.scores_table.all()
        total_answers = sum(score.get('total_correct_answers', 0) for score in all_scores)

        # Assuming an average of 10 questions per game
        return max(1, total_answers // 10)

    def get_average_score(self) -> float:
        """
        Get the average score across all players.

        Returns:
            Average score
        """
        all_scores = self.scores_table.all()

        if not all_scores:
            return 0.0

        total_score = sum(score.get('score', 0) for score in all_scores)
        return round(total_score / len(all_scores), 1)

    def get_highest_score(self) -> int:
        """
        Get the highest score achieved by any player.

        Returns:
            Highest score
        """
        all_scores = self.scores_table.all()

        if not all_scores:
            return 0

        return max(score.get('score', 0) for score in all_scores)
