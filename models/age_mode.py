# models/age_mode.py
from typing import Dict, Any, List, Optional
import random
from datetime import datetime
from .game_mode import GameMode

class AgeMode(GameMode):
    """
    Age game mode where players need to identify the age of an employee.
    This mode uses the birthDate field to calculate the age and offers 3 other choices
    at +/- 5 years from the real age.
    """
    @property
    def name(self) -> str:
        return "age"
    
    @property
    def description(self) -> str:
        return "Quel âge a la personne ? Devinez l'âge de la personne affichée"
    
    @property
    def template(self) -> str:
        return "age.html"
    
    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the age game mode.
        
        Args:
            user_id: Optional user ID. If not provided, a new user will be created.
            
        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id)
        
        # Get all employees
        all_employees = self.game_manager.employee_data.get_all_employees()
        
        # Filter employees with a birth date
        employees_with_birth_date = [emp for emp in all_employees if emp.get('birthDate')]
        
        # Store data and return initialization info
        data_id = self.game_manager.store_game_data(employees_with_birth_date)
        
        return {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': len(employees_with_birth_date)  # 1 point per correct age
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
        employees_with_birth_date = self.game_manager.get_game_data(data_id)
        
        # If all questions used, game over
        if len(used_indices) >= len(employees_with_birth_date):
            return {'game_over': True}
        
        # Select a random employee that hasn't been used yet
        available_indices = [i for i in range(len(employees_with_birth_date)) if i not in used_indices]
        if not available_indices:
            return {'game_over': True}
        
        selected_index = random.choice(available_indices)
        used_indices.append(selected_index)
        current_question += 1
        
        selected_employee = employees_with_birth_date[selected_index]
        
        # Calculate age
        birth_date_str = selected_employee.get('birthDate')
        if not birth_date_str:
            # If no birth date, skip this question
            return self.get_question_data(data_id, used_indices, current_question - 1)
        
        try:
            birth_date = datetime.strptime(birth_date_str.split('T')[0], '%Y-%m-%d')
            current_date = datetime.now()
            age = current_date.year - birth_date.year
            
            # Adjust for month and day
            if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
                age -= 1
                
            # Generate 3 other options (different from the correct one)
            # These should be +/- 5 years from the real age
            other_options = []
            while len(other_options) < 3:
                # Generate a random age within +/- 5 years of the real age
                option = age + random.randint(-5, 5)
                # Ensure age is positive and different from the correct one
                if option > 0 and option != age and option not in other_options:
                    other_options.append(option)
            
            # Add the correct answer
            choices = other_options + [age]
            random.shuffle(choices)
            
            return {
                'game_over': False,
                'employee': selected_employee,
                'age': age,
                'choices': choices,
                'current_question': current_question,
                'total_questions': len(employees_with_birth_date)
            }
        except Exception as e:
            # If error parsing date, skip this question
            print(f"Error calculating age: {e}")
            return self.get_question_data(data_id, used_indices, current_question - 1)
    
    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.
        
        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        correct_answer = kwargs.get('correct_answer', 0)
        
        if correct_answer:
            # Update the score
            self.game_manager.score_manager.update_score(
                user_id, 
                score_increment=1,
                company_correct=0,
                team_correct=0,
                name_correct=1,  # Count as name knowledge (personal info)
                position_correct=0
            )