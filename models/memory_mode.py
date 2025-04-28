# models/memory_mode.py
from typing import Dict, Any, List, Optional
from .game_mode import GameMode
import random

class MemoryMode(GameMode):
    """
    Memory game mode where players must match photos with names, similar to the classic memory card game.
    """
    @property
    def name(self) -> str:
        return "memory"
    
    @property
    def description(self) -> str:
        return "Mode mémoire : associez les photos avec les noms en retournant des cartes"
    
    @property
    def template(self) -> str:
        return "memory.html"
    
    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the memory game mode.
        
        Args:
            user_id: Optional user ID. If not provided, a new user will be created.
            
        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id)
        
        # Get all employees
        employees = self.game_manager.employee_data.get_all_employees()
        
        # Shuffle and select a subset of employees for the memory game
        random.shuffle(employees)
        selected_employees = employees[:8]  # Use 8 employees for 16 cards (8 pairs)
        
        # Create memory cards (pairs of images and names)
        memory_cards = []
        for employee in selected_employees:
            # Add image card
            memory_cards.append({
                'type': 'image',
                'value': employee.get('image_url', ''),
                'match_id': employee.get('name', ''),
                'display': employee.get('image_url', '')
            })
            
            # Add name card
            memory_cards.append({
                'type': 'name',
                'value': employee.get('name', ''),
                'match_id': employee.get('name', ''),
                'display': employee.get('name', '')
            })
        
        # Shuffle the cards
        random.shuffle(memory_cards)
        
        # Store data and return initialization info
        data_id = self.game_manager.store_game_data({
            'cards': memory_cards,
            'employees': selected_employees
        })
        
        return {
            'user_id': user_id,
            'data_id': data_id,
            'reverse_mode': False,
            'max_score': len(selected_employees)  # 1 point per matched pair
        }
    
    def get_question_data(self, data_id: int, used_indices: List[int], 
                         current_question: int) -> Dict[str, Any]:
        """
        Get data for the memory game.
        
        Args:
            data_id: ID of the game data
            used_indices: List of indices that have already been used
            current_question: Current question number
            
        Returns:
            Dictionary with memory game data
        """
        # Get the game data
        game_data = self.game_manager.get_game_data(data_id)
        if game_data is None:
            return {'game_over': True}
        
        # Check if this is a new game or a continuation
        if current_question == 0:
            # New game, return all cards
            return {
                'game_over': False,
                'cards': game_data['cards'],
                'current_question': 1,
                'total_pairs': len(game_data['employees'])
            }
        else:
            # Game already in progress, check if it's over
            if len(used_indices) >= len(game_data['employees']):
                return {'game_over': True}
            
            # Return the current state
            return {
                'game_over': False,
                'cards': game_data['cards'],
                'current_question': current_question,
                'total_pairs': len(game_data['employees'])
            }
    
    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.
        
        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        # In this mode, we count matched pairs
        matched_pairs = kwargs.get('matched_pairs', 0)
        
        # Update the score
        self.game_manager.score_manager.update_score(
            user_id, 
            score_increment=matched_pairs,
            company_correct=0,
            team_correct=0,
            name_correct=matched_pairs,  # Count each pair as a correct name
            position_correct=0
        )