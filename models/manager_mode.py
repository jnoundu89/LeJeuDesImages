# models/manager_mode.py
from typing import Dict, Any, List, Optional
import random
from datetime import datetime
from .game_mode import GameMode

class ManagerMode(GameMode):
    """
    Manager game mode where players need to identify who is the manager of a given employee.
    This mode is inspired by the reverse mode but with 4 images.
    """
    @property
    def name(self) -> str:
        return "manager"
    
    @property
    def description(self) -> str:
        return "Qui est le manager de qui ? Identifiez le manager de la personne affichée"
    
    @property
    def template(self) -> str:
        return "manager.html"
    
    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the manager game mode.
        
        Args:
            user_id: Optional user ID. If not provided, a new user will be created.
            
        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id)
        
        # Get all employees
        all_employees = self.game_manager.employee_data.get_all_employees()
        
        # Filter employees with a manager
        employees_with_manager = [emp for emp in all_employees if emp.get('manager_id') is not None]
        
        # Store data and return initialization info
        data_id = self.game_manager.store_game_data(employees_with_manager)
        
        return {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': len(employees_with_manager)  # 1 point per correct manager
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
        employees_with_manager = self.game_manager.get_game_data(data_id)
        
        # If all questions used, game over
        if len(used_indices) >= len(employees_with_manager):
            return {'game_over': True}
        
        # Select a random employee that hasn't been used yet
        available_indices = [i for i in range(len(employees_with_manager)) if i not in used_indices]
        if not available_indices:
            return {'game_over': True}
        
        selected_index = random.choice(available_indices)
        used_indices.append(selected_index)
        current_question += 1
        
        selected_employee = employees_with_manager[selected_index]
        manager_id = selected_employee.get('manager_id')
        
        # Find the manager in the employee list
        manager = next((emp for emp in self.game_manager.employee_data.get_all_employees() 
                        if emp.get('id') == manager_id), None)
        
        if not manager:
            # If manager not found, skip this question
            return self.get_question_data(data_id, used_indices, current_question - 1)
        
        # Get 3 other random managers (different from the correct one)
        other_managers = [emp for emp in self.game_manager.employee_data.get_all_employees() 
                         if emp.get('id') != manager_id and emp.get('id') in 
                         [e.get('manager_id') for e in employees_with_manager]]
        
        # If not enough other managers, use random employees
        if len(other_managers) < 3:
            additional_employees = [emp for emp in self.game_manager.employee_data.get_all_employees() 
                                  if emp.get('id') != manager_id and emp.get('id') != selected_employee.get('id')]
            if additional_employees:
                other_managers.extend(random.sample(additional_employees, 
                                                   min(3 - len(other_managers), len(additional_employees))))
        
        # Select choices
        if len(other_managers) >= 3:
            choices = random.sample(other_managers, 3)
        else:
            choices = other_managers
        
        # Add the correct answer
        choices.append(manager)
        random.shuffle(choices)
        
        return {
            'game_over': False,
            'employee': selected_employee,
            'manager': manager,
            'choices': choices,
            'current_question': current_question,
            'total_questions': len(employees_with_manager)
        }
    
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
                team_correct=1,  # Count as team knowledge
                name_correct=0,
                position_correct=1  # Count as position knowledge (manager position)
            )