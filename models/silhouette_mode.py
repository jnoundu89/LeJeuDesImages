# models/silhouette_mode.py
from typing import Dict, Any, List, Optional
from .game_mode import GameMode
import random

class SilhouetteMode(GameMode):
    """
    Silhouette game mode where players see only the silhouette of an employee and need to guess who it is.
    """
    @property
    def name(self) -> str:
        return "silhouette"
    
    @property
    def description(self) -> str:
        return "Mode Silhouette : identifiez la personne à partir de sa silhouette"
    
    @property
    def template(self) -> str:
        return "silhouette.html"
    
    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the silhouette game mode.
        
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
            'max_score': len(employees)  # 1 point per correct identification
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
        # Use the game manager to get question data
        question_data = self.game_manager.get_question_data(data_id, used_indices, current_question, False)
        
        # If game is over, return that info
        if question_data.get('game_over', False):
            return question_data
        
        # Get the selected employee data
        selected_employee = question_data.get('correct_values', {})
        
        # Get choices for name, filtered by sex
        sex_filter = {'sex': question_data.get('sex', 'man')}
        names = self.game_manager.employee_data.get_random_choices(
            'name', 
            selected_employee.get('name', ''), 
            filter_dict=sex_filter
        )
        
        # Add a hint about the employee (team or position)
        hint_type = random.choice(['team', 'position'])
        hint = selected_employee.get(hint_type, '')
        
        return {
            'game_over': False,
            'image_url': question_data.get('image_url', ''),
            'correct_name': selected_employee.get('name', ''),
            'name_choices': names,
            'hint_type': hint_type.capitalize(),
            'hint': hint,
            'current_question': current_question
        }
    
    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.
        
        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        # In this mode, we only care about the name
        correct_answer = kwargs.get('correct_answer', 0)
        
        if correct_answer:
            # Update the score and name statistic
            self.game_manager.score_manager.update_score(
                user_id, 
                score_increment=1,
                company_correct=0,
                team_correct=0,
                name_correct=1,
                position_correct=0
            )