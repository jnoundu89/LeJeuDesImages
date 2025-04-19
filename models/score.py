# models/score.py
from typing import Dict, Any, Optional
from tinydb import TinyDB, Query
import random
import logging

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
        
    def initialize_user(self, user_id: Optional[int] = None) -> int:
        """
        Initialize a new user or get an existing user.
        
        Args:
            user_id: Optional user ID. If not provided, a new user will be created.
            
        Returns:
            The user ID
        """
        if user_id is None:
            user_id = random.randint(1000, 9999)
            
        # Check if user exists
        user_score = self.scores_table.get(self.User.user_id == user_id)
        
        if user_score is None:
            # Create new user
            self.scores_table.insert({
                'user_id': user_id,
                'score': 0,
                'stats_company': 0,
                'stats_team': 0,
                'stats_name': 0,
                'stats_position': 0,
                'total_correct_answers': 0
            })
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
                    company_correct: int = 0, team_correct: int = 0, 
                    name_correct: int = 0, position_correct: int = 0) -> None:
        """
        Update a user's score.
        
        Args:
            user_id: The user ID
            score_increment: The amount to increment the score by
            company_correct: Whether the company answer was correct (0 or 1)
            team_correct: Whether the team answer was correct (0 or 1)
            name_correct: Whether the name answer was correct (0 or 1)
            position_correct: Whether the position answer was correct (0 or 1)
        """
        user_score = self.get_user_score(user_id)
        
        # Update score and statistics
        user_score['score'] += score_increment
        user_score['total_correct_answers'] += score_increment
        
        if company_correct:
            user_score['stats_company'] += 1
        if team_correct:
            user_score['stats_team'] += 1
        if name_correct:
            user_score['stats_name'] += 1
        if position_correct:
            user_score['stats_position'] += 1
            
        self.scores_table.update(user_score, self.User.user_id == user_id)
        logging.info(f"Score updated for user {user_id}: {user_score['score']}")
    
    def update_score_reverse_mode(self, user_id: int, correct_answer: int) -> None:
        """
        Update a user's score in reverse mode.
        
        Args:
            user_id: The user ID
            correct_answer: Whether the answer was correct (0 or 1)
        """
        user_score = self.get_user_score(user_id)
        
        if correct_answer:
            user_score['score'] += 1
            user_score['total_correct_answers'] += 1
            user_score['stats_name'] += 1  # In reverse mode, we're identifying names
            
        self.scores_table.update(user_score, self.User.user_id == user_id)
        logging.info(f"Score updated for user {user_id} in reverse mode: {user_score['score']}")
    
    def get_stats(self, user_id: int) -> Dict[str, int]:
        """
        Get the statistics for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary containing the user's statistics
        """
        user_score = self.get_user_score(user_id)
        
        return {
            'company': user_score.get('stats_company', 0),
            'team': user_score.get('stats_team', 0),
            'name': user_score.get('stats_name', 0),
            'position': user_score.get('stats_position', 0)
        }