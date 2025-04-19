# models/game_mode.py
from typing import Dict, Any, Callable, List, Optional
from abc import ABC, abstractmethod
from .game import GameManager

class GameMode(ABC):
    """
    Abstract base class for game modes.
    """
    def __init__(self, game_manager: GameManager):
        """
        Initialize the game mode.
        
        Args:
            game_manager: GameManager instance for managing the game
        """
        self.game_manager = game_manager
        
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the game mode.
        
        Returns:
            Name of the game mode
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get the description of the game mode.
        
        Returns:
            Description of the game mode
        """
        pass
    
    @property
    @abstractmethod
    def template(self) -> str:
        """
        Get the template to use for this game mode.
        
        Returns:
            Template name
        """
        pass
    
    @abstractmethod
    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the game mode.
        
        Args:
            user_id: Optional user ID. If not provided, a new user will be created.
            
        Returns:
            Dictionary with game initialization data
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.
        
        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        pass


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