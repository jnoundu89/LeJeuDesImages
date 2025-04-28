# models/arr_mode.py
from typing import Dict, Any, List, Optional
from .game_mode import GameMode
import random

class ARRMode(GameMode):
    """
    ARR (Annual Recurring Revenue) game mode where players must reach +15% ARR objectives
    to earn employee bonuses. This is a hidden easter egg mode.
    """
    @property
    def name(self) -> str:
        return "arr"

    @property
    def description(self) -> str:
        return "Mode ARR : atteignez +15% d'ARR pour obtenir une prime de participation"

    @property
    def template(self) -> str:
        return "arr_mode.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the ARR game mode.

        Args:
            user_id: Optional user ID. If not provided, a new user will be created.

        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id)

        # Generate initial ARR value (between 1,000,000 and 5,000,000)
        initial_arr = random.randint(1000000, 5000000)

        # Calculate target ARR (15% increase)
        target_arr = initial_arr * 1.15

        # Generate game data
        game_data = {
            'initial_arr': initial_arr,
            'current_arr': initial_arr,
            'target_arr': target_arr,
            'current_month': 1,
            'max_months': 12,  # 12 months to reach the target
            'actions_taken': [],
            'events': self._generate_events(),
            'available_actions': self._generate_actions()
        }

        # Store data and return initialization info
        data_id = self.game_manager.store_game_data(game_data)

        return {
            'user_id': user_id,
            'data_id': data_id,
            'reverse_mode': False,
            'max_score': 1  # Binary win/lose
        }

    def get_question_data(self, data_id: int, used_indices: List[int], 
                         current_question: int) -> Dict[str, Any]:
        """
        Get data for the current state of the ARR game.

        Args:
            data_id: ID of the game data
            used_indices: List of indices that have already been used
            current_question: Current question number

        Returns:
            Dictionary with game state data
        """
        # Get the game data
        game_data = self.game_manager.get_game_data(data_id)
        if game_data is None:
            return {'game_over': True}

        # Check if game is over (reached max months or target ARR)
        if game_data['current_month'] > game_data['max_months']:
            # Game over - check if target was reached
            success = game_data['current_arr'] >= game_data['target_arr']
            percentage_increase = ((game_data['current_arr'] - game_data['initial_arr']) / game_data['initial_arr']) * 100

            # Format values for display
            formatted_actions = []
            for action in game_data['actions_taken']:
                formatted_action = action.copy()
                formatted_action['arr_change_formatted'] = f"{action['arr_change']:+,.0f}"
                formatted_actions.append(formatted_action)

            return {
                'game_over': True,
                'success': success,
                'initial_arr': game_data['initial_arr'],
                'current_arr': game_data['current_arr'],
                'target_arr': game_data['target_arr'],
                'percentage_increase': percentage_increase,
                'actions_taken': formatted_actions,
                # Formatted values for display
                'initial_arr_formatted': f"{game_data['initial_arr']:,.0f}",
                'current_arr_formatted': f"{game_data['current_arr']:,.0f}",
                'target_arr_formatted': f"{game_data['target_arr']:,.0f}",
                'percentage_increase_formatted': f"{percentage_increase:.2f}"
            }

        # Get random event for this month if not already processed
        event = None
        if current_question == game_data['current_month'] - 1:
            # No event for the first turn
            pass
        elif len(used_indices) < len(game_data['events']):
            # Get a random event
            available_indices = [i for i in range(len(game_data['events'])) if i not in used_indices]
            if available_indices:
                event_index = random.choice(available_indices)
                used_indices.append(event_index)
                event = game_data['events'][event_index]

                # Apply event effect
                game_data['current_arr'] = max(0, game_data['current_arr'] + event['arr_change'])

        # Calculate percentage increase
        percentage = ((game_data['current_arr'] - game_data['initial_arr']) / game_data['initial_arr']) * 100

        # Format values for display
        formatted_actions = []
        for action in game_data['actions_taken']:
            formatted_action = action.copy()
            formatted_action['arr_change_formatted'] = f"{action['arr_change']:+,.0f}"
            formatted_actions.append(formatted_action)

        formatted_available_actions = []
        for action in game_data['available_actions']:
            formatted_action = action.copy()
            formatted_action['arr_change_formatted'] = f"{action['arr_change']:+,.0f}"
            formatted_available_actions.append(formatted_action)

        # Calculate progress bar width (clamped between 0-100%)
        progress_width = min(max(percentage / 15 * 100, 0), 100)

        return {
            'game_over': False,
            'data_id': data_id,
            'current_month': game_data['current_month'],
            'max_months': game_data['max_months'],
            'initial_arr': game_data['initial_arr'],
            'current_arr': game_data['current_arr'],
            'target_arr': game_data['target_arr'],
            'percentage': percentage,
            'event': event,
            'available_actions': formatted_available_actions,
            'actions_taken': formatted_actions,
            # Formatted values for display
            'initial_arr_formatted': f"{game_data['initial_arr']:,.0f}",
            'current_arr_formatted': f"{game_data['current_arr']:,.0f}",
            'target_arr_formatted': f"{game_data['target_arr']:,.0f}",
            'percentage_formatted': f"{percentage:.2f}",
            'progress_width': progress_width
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.

        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        # Get the game data
        data_id = kwargs.get('data_id', 0)
        action_index = kwargs.get('action_index', -1)

        game_data = self.game_manager.get_game_data(data_id)
        if game_data is None:
            return

        # Apply the selected action
        if 0 <= action_index < len(game_data['available_actions']):
            action = game_data['available_actions'][action_index]

            # Apply action effect
            game_data['current_arr'] = max(0, game_data['current_arr'] + action['arr_change'])

            # Record the action
            game_data['actions_taken'].append({
                'month': game_data['current_month'],
                'action': action['name'],
                'description': action['description'],
                'arr_change': action['arr_change']
            })

            # Move to next month
            game_data['current_month'] += 1

            # Update the game data
            self.game_manager.update_game_data(data_id, game_data)

            # Check if game is over and successful
            if game_data['current_month'] > game_data['max_months'] and game_data['current_arr'] >= game_data['target_arr']:
                # Update the score (1 point for success)
                self.game_manager.score_manager.update_score(
                    user_id, 
                    score_increment=1,
                    company_correct=1,  # Count as company knowledge
                    team_correct=0,
                    name_correct=0,
                    position_correct=0
                )

    def _generate_events(self) -> List[Dict[str, Any]]:
        """
        Generate random events that can occur during the game.

        Returns:
            List of event dictionaries
        """
        events = [
            {
                'name': 'Crise économique',
                'description': 'Une crise économique affecte le marché. Votre ARR diminue de 5%.',
                'arr_change': lambda arr: -0.05 * arr
            },
            {
                'name': 'Nouveau concurrent',
                'description': 'Un nouveau concurrent entre sur le marché. Votre ARR diminue de 3%.',
                'arr_change': lambda arr: -0.03 * arr
            },
            {
                'name': 'Opportunité de marché',
                'description': 'Une nouvelle opportunité de marché s\'ouvre. Votre ARR augmente de 4%.',
                'arr_change': lambda arr: 0.04 * arr
            },
            {
                'name': 'Partenariat stratégique',
                'description': 'Vous concluez un partenariat stratégique. Votre ARR augmente de 6%.',
                'arr_change': lambda arr: 0.06 * arr
            },
            {
                'name': 'Problème technique',
                'description': 'Un problème technique affecte votre service. Votre ARR diminue de 4%.',
                'arr_change': lambda arr: -0.04 * arr
            },
            {
                'name': 'Reconnaissance du marché',
                'description': 'Votre entreprise est reconnue comme leader du marché. Votre ARR augmente de 5%.',
                'arr_change': lambda arr: 0.05 * arr
            }
        ]

        # Process the lambda functions to get actual values
        processed_events = []
        for event in events:
            processed_events.append({
                'name': event['name'],
                'description': event['description'],
                'arr_change': 0  # Will be calculated when the event occurs
            })

        return processed_events

    def _generate_actions(self) -> List[Dict[str, Any]]:
        """
        Generate actions that the player can take during the game.

        Returns:
            List of action dictionaries
        """
        return [
            {
                'name': 'Lancer une campagne marketing',
                'description': 'Investir dans une campagne marketing pour attirer de nouveaux clients.',
                'arr_change': 100000,  # Fixed amount
                'success_rate': 0.8
            },
            {
                'name': 'Améliorer le produit',
                'description': 'Investir dans l\'amélioration du produit pour fidéliser les clients existants.',
                'arr_change': 80000,
                'success_rate': 0.9
            },
            {
                'name': 'Réduire les prix',
                'description': 'Réduire les prix pour attirer plus de clients, mais avec une marge plus faible.',
                'arr_change': 50000,
                'success_rate': 0.7
            },
            {
                'name': 'Augmenter les prix',
                'description': 'Augmenter les prix pour améliorer la marge, mais risquer de perdre des clients.',
                'arr_change': -30000,  # Initial negative impact
                'success_rate': 0.4
            },
            {
                'name': 'Embaucher une équipe commerciale',
                'description': 'Investir dans une équipe commerciale pour augmenter les ventes.',
                'arr_change': 150000,
                'success_rate': 0.75
            },
            {
                'name': 'Développer un nouveau produit',
                'description': 'Investir dans le développement d\'un nouveau produit pour diversifier l\'offre.',
                'arr_change': 200000,
                'success_rate': 0.6
            },
            {
                'name': 'Expansion internationale',
                'description': 'Étendre l\'activité à de nouveaux marchés internationaux.',
                'arr_change': 250000,
                'success_rate': 0.5
            },
            {
                'name': 'Optimiser les coûts',
                'description': 'Réduire les coûts opérationnels pour améliorer la rentabilité.',
                'arr_change': 70000,
                'success_rate': 0.85
            }
        ]
