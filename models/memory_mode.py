# models/memory_mode.py
import random
from typing import Any, Dict, List, Optional

from .game_mode import GameMode


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
            # Create full name from first_name and last_name
            full_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()

            # Add image card
            memory_cards.append({
                'type': 'image',
                'value': employee.get('photo', ''),
                'match_id': full_name,
                'display': employee.get('photo', '')
            })

            # Add name card
            memory_cards.append({
                'type': 'name',
                'value': full_name,
                'match_id': full_name,
                'display': full_name
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
            # Check if the level is completed (all pairs found) and we need to generate new cards
            matched_pairs = int(len(used_indices))
            if matched_pairs >= len(game_data['employees']) and matched_pairs > 0:
                # Generate new set of employees and cards for the next level
                employees = self.game_manager.employee_data.get_all_employees()

                # Shuffle and select a subset of employees for the memory game
                # Ensure we get different employees than before if possible
                random.shuffle(employees)
                previous_employees = game_data['employees']
                new_employees = []

                # Try to select employees that weren't in the previous set
                for employee in employees:
                    if len(new_employees) >= 8:
                        break

                    # Check if this employee was in the previous set
                    was_in_previous = False
                    for prev_emp in previous_employees:
                        if (employee.get('first_name') == prev_emp.get('first_name') and
                            employee.get('last_name') == prev_emp.get('last_name')):
                            was_in_previous = True
                            break

                    if not was_in_previous:
                        new_employees.append(employee)

                # If we couldn't find enough new employees, add some from the previous set
                if len(new_employees) < 8:
                    random.shuffle(employees)
                    for employee in employees:
                        if len(new_employees) >= 8:
                            break
                        if employee not in new_employees:
                            new_employees.append(employee)

                # Create memory cards (pairs of images and names)
                memory_cards = []
                for employee in new_employees:
                    # Create full name from first_name and last_name
                    full_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()

                    # Add image card
                    memory_cards.append({
                        'type': 'image',
                        'value': employee.get('photo', ''),
                        'match_id': full_name,
                        'display': employee.get('photo', '')
                    })

                    # Add name card
                    memory_cards.append({
                        'type': 'name',
                        'value': full_name,
                        'match_id': full_name,
                        'display': full_name
                    })

                # Shuffle the cards
                random.shuffle(memory_cards)

                # Update the game data with new cards and employees
                game_data['cards'] = memory_cards
                game_data['employees'] = new_employees
                self.game_manager.update_game_data(data_id, game_data)

                # Reset used_indices for the new level
                used_indices = []

                # Return the new cards
                return {
                    'game_over': False,
                    'cards': memory_cards,
                    'current_question': current_question + 1,
                    'total_pairs': len(new_employees)
                }

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

    def handle_answer(self, user_id: int, form_data: dict, session_data: dict) -> dict:
        matched_pairs = int(form_data.get('matched_pairs', 0))
        self.update_score(user_id, matched_pairs=matched_pairs)
        if matched_pairs > 0:
            return {'used_indices': list(range(matched_pairs))}
        return {}

    def update_score(self, user_id: int, **kwargs) -> None:
        matched_pairs = kwargs.get('matched_pairs', 0)
        self.game_manager.score_manager.update_score(
            user_id,
            score_increment=matched_pairs,
            stat_updates={'name': matched_pairs},
        )
