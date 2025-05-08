# models/speed_mode.py
from typing import Dict, Any, List, Optional
from .game_mode import GameMode
import random

class SpeedMode(GameMode):
    """
    Speed game mode where players have a limited time to identify as many employees as possible.
    The faster they answer, the more points they earn.
    """
    @property
    def name(self) -> str:
        return "speed"
    
    @property
    def description(self) -> str:
        return "Mode vitesse : identifiez un maximum d'employés en un temps limité, plus vous êtes rapide, plus vous gagnez de points"
    
    @property
    def template(self) -> str:
        return "speed.html"
    
    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the speed game mode.
        
        Args:
            user_id: Optional user ID. If not provided, a new user will be created.
            
        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id)
        
        # Get all employees
        employees = self.game_manager.employee_data.get_all_employees()
        random.shuffle(employees)
        
        # Store data and return initialization info
        data_id = self.game_manager.store_game_data(employees)
        
        return {
            'user_id': user_id,
            'data_id': data_id,
            'reverse_mode': False,
            'max_score': len(employees) * 3,  # Maximum 3 points per employee (if answered very quickly)
            'time_limit': 60  # 60 seconds time limit
        }
    
    def get_question_data(self, data_id: int, used_indices: List[int], 
                         current_question: int) -> Dict[str, Any]:
        """
        Get data for the current question.
        
        Args:
            data_id: ID of the game data
            used_indices: List of indices that have already been used
            current_question: Current question number
            
        Returns:
            Dictionary with question data
        """
        # Get the game data
        game_data = self.game_manager.get_game_data(data_id)
        
        # If all indices have been used, return None
        if len(used_indices) >= len(game_data):
            return {'game_over': True}
        
        # Get all available indices
        all_indices = list(range(len(game_data)))
        available_indices = [i for i in all_indices if i not in used_indices]
        
        if not available_indices:
            return {'game_over': True}
        
        # Get the next index
        index = available_indices[0]
        used_indices.append(index)
        current_question += 1
        
        # Get the selected employee
        selected_employee = game_data[index]
        
        # Get correct values
        correct_values = {
            'name': selected_employee['name'],
        }
        
        # For name choices, filter by sex for more realistic choices
        sex_filter = {'sex': selected_employee['sex']}
        names = self.game_manager.employee_data.get_random_choices('name', correct_values['name'], filter_dict=sex_filter)
        
        return {
            'game_over': False,
            'image_url': selected_employee['image_url'],
            'correct_name': correct_values['name'],
            'name_choices': names,
            'current_question': current_question,
            'total_questions': len(game_data)
        }
    
    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.
        
        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        correct_answer = kwargs.get('correct_answer', 0)
        response_time = kwargs.get('response_time', 0)  # Time in milliseconds
        
        if correct_answer:
            # Calculate score based on response time
            # Faster responses get more points (max 3 points if < 1 second)
            if response_time < 1000:  # Less than 1 second
                score_increment = 3
            elif response_time < 3000:  # Less than 3 seconds
                score_increment = 2
            else:  # More than 3 seconds
                score_increment = 1
                
            # Update the score
            self.game_manager.score_manager.update_score(
                user_id, 
                score_increment=score_increment,
                company_correct=0,
                team_correct=0,
                name_correct=1,
                position_correct=0
            )