# models/clue_mode.py
from typing import Dict, Any, List, Optional
from .game_mode import GameMode
import random

class ClueMode(GameMode):
    """
    Clue game mode where players receive progressive hints (initials, team, function)
    and must guess who the person is with the fewest hints possible to maximize their score.
    """
    @property
    def name(self) -> str:
        return "clue"

    @property
    def description(self) -> str:
        return "Mode indices : devinez qui est la personne avec le minimum d'indices"

    @property
    def template(self) -> str:
        return "clue.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the clue game mode.

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
            'max_score': len(employees) * 3  # Maximum 3 points per employee (fewer hints = more points)
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
        # Use the game manager to get question data (with reverse_mode=False)
        question_data = self.game_manager.get_question_data(data_id, used_indices, current_question, False)

        # If game is over, return that info
        if question_data.get('game_over', False):
            return question_data

        # Get the selected employee data directly from the game data
        game_data = self.game_manager.get_game_data(data_id)
        index = used_indices[-1]  # Get the last used index
        selected_employee = game_data[index]

        # Create full name by joining firstName and lastName
        first_name = selected_employee['firstName']
        last_name = selected_employee['lastName']
        full_name = f"{first_name} {last_name}"

        # Generate clues
        clues = self._generate_clues(selected_employee)

        # Get choices for name only, filtered by sex
        sex_filter = {'sex': selected_employee['sex']}

        # Get other employees with the same sex
        filtered_employees = self.game_manager.employee_data.get_filtered_employees(sex_filter)

        # Remove the selected employee from the filtered list
        other_employees = [e for e in filtered_employees if e['firstName'] != first_name or e['lastName'] != last_name]

        # Select 3 random employees if we have enough
        if len(other_employees) >= 3:
            other_employees = random.sample(other_employees, 3)

        # Create full names for all employees
        names = [full_name]
        for employee in other_employees:
            names.append(f"{employee['firstName']} {employee['lastName']}")

        # Shuffle the names to randomize the order
        random.shuffle(names)

        return {
            'game_over': False,
            'image_url': question_data.get('image_url', ''),
            'correct_name': full_name,
            'name_choices': names,
            'current_question': current_question,
            'clues': clues
        }

    def _generate_clues(self, employee: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Generate a list of clues for the employee.

        Args:
            employee: Dictionary with employee data

        Returns:
            List of clue dictionaries
        """
        clues = []

        # Clue 1: Initials
        first_name = employee.get('firstName', '')
        last_name = employee.get('lastName', '')
        full_name = f"{first_name} {last_name}"

        if full_name:
            initials = ''.join([word[0] for word in full_name.split() if word])
            clues.append({
                'type': 'initials',
                'text': f"Initiales : {initials}",
                'level': 1,
                'points': 3
            })

        # Clue 2: Team
        team = employee.get('department_name', '')
        if team:
            clues.append({
                'type': 'team',
                'text': f"Équipe : {team}",
                'level': 2,
                'points': 2
            })

        # Clue 3: Position
        position = employee.get('jobTitle', '')
        if position:
            clues.append({
                'type': 'position',
                'text': f"Poste : {position}",
                'level': 3,
                'points': 1
            })

        # Clue 4: Company (if available)
        company = employee.get('legalEntity_name', '')
        if company:
            clues.append({
                'type': 'company',
                'text': f"Entreprise : {company}",
                'level': 4,
                'points': 1
            })

        return clues

    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.

        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        # In this mode, score depends on how many clues were used
        correct_answer = kwargs.get('correct_answer', 0)
        clues_used = kwargs.get('clues_used', 0)

        if correct_answer:
            # Calculate score based on clues used (fewer clues = higher score)
            # Maximum 3 points if guessed with 1 clue, minimum 1 point if all clues used
            max_clues = 3  # Assuming we have 3 clues max
            score_increment = max(1, max_clues - clues_used + 1) if clues_used > 0 else max_clues

            # Update the score and name statistic
            self.game_manager.score_manager.update_score(
                user_id, 
                score_increment=score_increment,
                company_correct=0,
                team_correct=0,
                name_correct=1,
                position_correct=0
            )
