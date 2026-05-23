# models/emoji_challenge_mode.py
import random
from typing import Any, ClassVar, Dict, List

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class EmojiChallengeMode(GameMode):
    """
    Emoji Challenge game mode where players see a series of emojis that represent
    characteristics of an employee (team, position, etc.) and need to guess who it is.
    """

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name', 'sex', 'team', 'job_title']
    difficulty: ClassVar[int] = 2
    estimated_duration_sec: ClassVar[int] = 90
    tags: ClassVar[List[str]] = ['devinette']
    icon: ClassVar[str] = 'fa-face-smile'
    preview_type: ClassVar[str] = 'emoji'
    experimental: ClassVar[bool] = True

    @property
    def name(self) -> str:
        return 'emoji_challenge'

    @property
    def display_name(self):
        return _l("Défi Emoji")

    @property
    def description(self):
        return _l("Mode Défi Emoji : devinez qui est la personne représentée par ces emojis")

    @property
    def template(self) -> str:
        return 'emoji_challenge.html'

    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        emoji_clues = self._generate_emoji_clues(selected)

        return {
            'game_over': False,
            'image_url': selected['photo'],
            'correct_name': self._make_full_name(selected),
            'name_choices': self._get_name_choices(selected),
            'emoji_clues': emoji_clues,
            'current_question': current_question,
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        correct_answer = kwargs.get('correct_answer', 0)
        if correct_answer:
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=1,
                stat_updates={'name': 1},
            )

    def _generate_emoji_clues(self, employee: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate emoji clues based on employee data.

        Args:
            employee: Dictionary with employee data

        Returns:
            Dictionary with emoji clues for different attributes
        """
        # Generic company emoji (fallback: 🏢)
        company_emojis = {}

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
        position = employee.get('job_title', '')

        # Create full name for length calculation
        first_name = employee.get('first_name', '')
        last_name = employee.get('last_name', '')
        full_name = f"{first_name} {last_name}"

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
        name_length = len(full_name)
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
