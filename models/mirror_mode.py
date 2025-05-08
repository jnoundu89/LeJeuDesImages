# models/mirror_mode.py
from typing import Dict, Any, List, Optional
from .game_mode import GameMode
import random

class MirrorMode(GameMode):
    """
    Mirror game mode where players see a horizontally flipped (mirrored) image of an employee
    and need to guess who it is. This can be surprisingly challenging as our brains are used
    to seeing faces in a specific orientation.
    """
    @property
    def name(self) -> str:
        return "mirror"
    
    @property
    def description(self) -> str:
        return "Mode Miroir : identifiez la personne dont l'image est inversée horizontalement"
    
    @property
    def template(self) -> str:
        return "mirror.html"
    
    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the mirror game mode.
        
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
        
        # Add a fun fact about mirror perception
        mirror_facts = [
            "Saviez-vous que notre cerveau a du mal à reconnaître les visages inversés?",
            "Les visages en miroir peuvent sembler très différents de la réalité!",
            "Notre cerveau est habitué à voir les visages dans un certain sens.",
            "L'effet miroir peut rendre méconnaissable même un visage familier!",
            "Les asymétries faciales deviennent plus évidentes quand l'image est inversée."
        ]
        
        return {
            'game_over': False,
            'image_url': question_data.get('image_url', ''),
            'correct_name': selected_employee.get('name', ''),
            'name_choices': names,
            'mirror_fact': random.choice(mirror_facts),
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