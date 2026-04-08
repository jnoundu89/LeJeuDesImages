# models/quiz_mode.py
import random
from typing import Any, Dict, List, Optional

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class QuizMode(GameMode):
    """
    Quiz game mode where players answer various questions about their colleagues
    (who works on which project, who has which skill, etc.).
    """
    @property
    def name(self) -> str:
        return "quiz"

    @property
    def description(self) -> str:
        return _l("Mode quiz : répondez à des questions variées sur vos collègues")

    @property
    def template(self) -> str:
        return "quiz.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the quiz game mode.

        Args:
            user_id: Optional user ID. If not provided, a new user will be created.

        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id)

        # Get all employees
        employees = self.game_manager.employee_data.get_all_employees()

        # Generate quiz questions
        questions = self._generate_questions(employees)

        # Store data and return initialization info
        data_id = self.game_manager.store_game_data({
            'questions': questions,
            'employees': employees
        })

        return {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': len(questions)  # 1 point per correct answer
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
        if game_data is None:
            return {'game_over': True}

        # Check if we've used all questions
        if len(used_indices) >= len(game_data['questions']):
            return {'game_over': True}

        # Get the next unused index
        available_indices = [i for i in range(len(game_data['questions'])) if i not in used_indices]
        if not available_indices:
            return {'game_over': True}

        # Select a random index from available indices
        index = random.choice(available_indices)
        used_indices.append(index)

        # Get the question
        question = game_data['questions'][index]

        return {
            'game_over': False,
            'question_text': question['text'],
            'question_type': question['type'],
            'choices': question['choices'],
            'correct_answer': question['correct_answer'],
            'image_url': question.get('image_url', ''),
            'current_question': current_question + 1
        }

    def _generate_questions(self, employees: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Generate quiz questions based on employee data.

        Args:
            employees: List of employee dictionaries

        Returns:
            List of question dictionaries
        """
        questions = []

        # Map CSV column names to expected fields
        mapped_employees = []
        for employee in employees:
            mapped_employee = {
                'team': employee.get('team', 'Unknown'),
                'name': f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
                'position': employee.get('job_title', ''),
                'image_url': employee.get('photo', '')
            }
            mapped_employees.append(mapped_employee)

        # Group employees by team
        teams = {}
        for employee in mapped_employees:
            team = employee.get('team', 'Unknown')
            if team not in teams:
                teams[team] = []
            teams[team].append(employee)

        # Generate "Who is in this team?" questions
        for team, members in teams.items():
            if len(members) >= 3:  # Only for teams with at least 3 members
                # Select a random member from the team
                selected_member = random.choice(members)

                # Create choices (1 correct + 3 incorrect)
                all_employees = [e for e in mapped_employees if e.get('team', '') != team]
                random.shuffle(all_employees)
                incorrect_choices = [e.get('name', '') for e in all_employees[:3]]

                choices = [selected_member.get('name', '')] + incorrect_choices
                random.shuffle(choices)

                questions.append({
                    'type': 'team_member',
                    'text': f"Qui fait partie de l'équipe {team}?",
                    'choices': choices,
                    'correct_answer': selected_member.get('name', ''),
                    'image_url': selected_member.get('image_url', '')
                })

        # Generate "What team is this person in?" questions
        for employee in mapped_employees:
            name = employee.get('name', '')
            team = employee.get('team', '')

            if team:
                # Create choices (1 correct + 3 incorrect)
                all_teams = list(teams.keys())
                incorrect_choices = [t for t in all_teams if t != team]
                random.shuffle(incorrect_choices)

                choices = [team] + incorrect_choices[:3]
                random.shuffle(choices)

                questions.append({
                    'type': 'employee_team',
                    'text': f"Dans quelle équipe travaille {name}?",
                    'choices': choices,
                    'correct_answer': team,
                    'image_url': employee.get('image_url', '')
                })

        # Generate "What is this person's position?" questions
        for employee in mapped_employees:
            name = employee.get('name', '')
            position = employee.get('position', '')

            if position:
                # Get all unique positions
                all_positions = list(set(e.get('position', '') for e in mapped_employees if e.get('position', '')))
                incorrect_choices = [p for p in all_positions if p != position]
                random.shuffle(incorrect_choices)

                choices = [position] + incorrect_choices[:3]
                random.shuffle(choices)

                questions.append({
                    'type': 'employee_position',
                    'text': f"Quel est le poste de {name}?",
                    'choices': choices,
                    'correct_answer': position,
                    'image_url': employee.get('image_url', '')
                })

        # Shuffle all questions
        random.shuffle(questions)

        # Limit to 10 questions for a reasonable quiz length
        return questions[:10]

    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.

        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        # In this mode, we count correct quiz answers
        correct_answer = kwargs.get('correct_answer', 0)

        if correct_answer:
            # Update the score
            self.game_manager.score_manager.update_score(
                user_id,
                score_increment=1,
                stat_updates={'team': 1},
            )
