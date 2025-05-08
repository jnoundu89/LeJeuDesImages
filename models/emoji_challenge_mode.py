# models/emoji_challenge_mode.py
from typing import Dict, Any, List, Optional
from .game_mode import GameMode
import random

class EmojiChallengeMode(GameMode):
    """
    Emoji Challenge game mode where players see a series of emojis that represent
    characteristics of an employee (team, position, etc.) and need to guess who it is.
    """
    @property
    def name(self) -> str:
        return "emoji_challenge"
    
    @property
    def description(self) -> str:
        return "Mode Défi Emoji : devinez qui est la personne représentée par ces emojis"
    
    @property
    def template(self) -> str:
        return "emoji_challenge.html"
    
    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the emoji challenge game mode.
        
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
        
        # Create emoji clues based on employee data
        emoji_clues = self._generate_emoji_clues(selected_employee)
        
        return {
            'game_over': False,
            'image_url': question_data.get('image_url', ''),
            'correct_name': selected_employee.get('name', ''),
            'name_choices': names,
            'emoji_clues': emoji_clues,
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
    
    def _generate_emoji_clues(self, employee: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate emoji clues based on employee data.
        
        Args:
            employee: Dictionary with employee data
            
        Returns:
            Dictionary with emoji clues for different attributes
        """
        # Map companies to emojis
        company_emojis = {
            "Infolegale": "🏢",
            "Ellisphere": "🌐",
            "Altares": "📊",
            "Dun & Bradstreet": "🌍",
            "Pouey International": "🔍"
        }
        
        # Map teams to emojis
        team_emojis = {
            "Tech": "💻",
            "Marketing": "📣",
            "Sales": "💼",
            "Finance": "💰",
            "HR": "👥",
            "Product": "📱",
            "Management": "👔",
            "Customer Success": "🤝",
            "Data": "📈",
            "Design": "🎨",
            "Operations": "⚙️"
        }
        
        # Map positions to emojis
        position_emojis = {
            "Developer": "👨‍💻",
            "Engineer": "🔧",
            "Manager": "📋",
            "Director": "👑",
            "Analyst": "🔎",
            "Specialist": "🧠",
            "Consultant": "💬",
            "Designer": "✏️",
            "Coordinator": "🔄",
            "Assistant": "📝",
            "CEO": "🌟",
            "CTO": "🚀",
            "CFO": "💵",
            "COO": "⚖️"
        }
        
        # Generate emoji clues
        company = employee.get('company', '')
        team = employee.get('team', '')
        position = employee.get('position', '')
        
        # Default emojis if not found in the mapping
        company_emoji = company_emojis.get(company, "🏢")
        team_emoji = team_emojis.get(team, "👥")
        
        # For position, try to find a partial match
        position_emoji = "👤"  # Default
        for key, emoji in position_emojis.items():
            if key.lower() in position.lower():
                position_emoji = emoji
                break
        
        # Add some personality emojis based on name length, team, etc.
        personality_emojis = []
        
        # Add emoji based on name length
        name_length = len(employee.get('name', ''))
        if name_length < 10:
            personality_emojis.append("🧸")  # Short name
        else:
            personality_emojis.append("📚")  # Long name
        
        # Add emoji based on team
        if "Tech" in team or "Data" in team:
            personality_emojis.append("🤓")  # Tech/Data person
        elif "Marketing" in team or "Design" in team:
            personality_emojis.append("🎭")  # Creative person
        elif "Sales" in team or "Customer" in team:
            personality_emojis.append("🗣️")  # Talkative person
        elif "Management" in team or "Director" in position:
            personality_emojis.append("🧠")  # Strategic thinker
        else:
            personality_emojis.append("😎")  # Cool person
        
        # Add random fun emoji
        fun_emojis = ["🎮", "🎯", "🎪", "🎭", "🎨", "🎬", "🎤", "🎧", "🎸", "🎹", "🎺", "🎻"]
        personality_emojis.append(random.choice(fun_emojis))
        
        return {
            'company': company_emoji,
            'team': team_emoji,
            'position': position_emoji,
            'personality': ' '.join(personality_emojis)
        }