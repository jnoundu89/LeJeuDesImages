# models/arr_mode.py
import random
from typing import Any, Dict, List, Optional

from .game_mode import GameMode


class ARRMode(GameMode):
    """
    ARR (Arcade Retro Racing) game mode where players control a car in a retro-style racing game.
    This is a hidden easter egg mode.
    """
    @property
    def name(self) -> str:
        return "arr"

    @property
    def description(self) -> str:
        return "Mode ARR : Arcade Retro Racing - Évitez les obstacles et atteignez la ligne d'arrivée !"

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

        # Generate game data
        game_data = {
            'player': {
                'position': 2,  # Middle lane (0-4)
                'speed': 1,     # Initial speed
                'distance': 0,  # Distance traveled
                'boost': 0,     # Boost meter (0-100)
                'lives': 3      # Number of lives
            },
            'track': {
                'length': 1000,  # Track length
                'obstacles': self._generate_obstacles(1000),  # Generate obstacles
                'power_ups': self._generate_power_ups(1000),  # Generate power-ups
                'current_segment': 0  # Current track segment
            },
            'game_state': {
                'started': False,
                'game_over': False,
                'win': False,
                'score': 0,
                'time': 0
            }
        }

        # Store data and return initialization info
        data_id = self.game_manager.store_game_data(game_data)

        return {
            'user_id': user_id,
            'data_id': data_id,
            'reverse_mode': False,
            'max_score': 1000  # Maximum possible score
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

        # Check if game_data is a dictionary and has the expected structure
        if not isinstance(game_data, dict) or 'game_state' not in game_data:
            # If game_data is not properly structured, return game over
            return {'game_over': True}

        # Check if game is over
        if game_data['game_state']['game_over']:
            return {
                'game_over': True,
                'win': game_data['game_state']['win'],
                'score': game_data['game_state']['score'],
                'distance': game_data['player']['distance'],
                'time': game_data['game_state']['time']
            }

        # Get visible obstacles and power-ups for the current segment
        visible_range = 20  # How far ahead the player can see
        current_segment = game_data['track']['current_segment']
        visible_obstacles = [
            obs for obs in game_data['track']['obstacles']
            if current_segment <= obs['position'] < current_segment + visible_range
        ]
        visible_power_ups = [
            pu for pu in game_data['track']['power_ups']
            if current_segment <= pu['position'] < current_segment + visible_range
        ]

        # Calculate progress percentage
        progress = (game_data['player']['distance'] / game_data['track']['length']) * 100
        progress = min(max(progress, 0), 100)  # Clamp between 0-100%

        return {
            'game_over': False,
            'data_id': data_id,
            'player': game_data['player'],
            'track_length': game_data['track']['length'],
            'visible_obstacles': visible_obstacles,
            'visible_power_ups': visible_power_ups,
            'current_segment': current_segment,
            'progress': progress,
            'score': game_data['game_state']['score'],
            'time': game_data['game_state']['time'],
            'game_started': game_data['game_state']['started']
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
        action = kwargs.get('action', '')

        game_data = self.game_manager.get_game_data(data_id)
        if game_data is None:
            return

        # Check if game_data is a dictionary and has the expected structure
        if not isinstance(game_data, dict) or 'game_state' not in game_data:
            # Initialize a new game if game_data is not properly structured
            game_data = self.initialize(user_id)
            data_id = game_data['data_id']
            game_data = self.game_manager.get_game_data(data_id)
            if not isinstance(game_data, dict) or 'game_state' not in game_data:
                # If still not properly structured, return to avoid errors
                return

        # Start the game if not started
        if not game_data['game_state']['started'] and action == 'start':
            game_data['game_state']['started'] = True
            self.game_manager.update_game_data(data_id, game_data)
            return

        # Process player action
        if game_data['game_state']['started'] and not game_data['game_state']['game_over']:
            # Handle player movement
            if action == 'left' and game_data['player']['position'] > 0:
                game_data['player']['position'] -= 1
            elif action == 'right' and game_data['player']['position'] < 4:
                game_data['player']['position'] += 1
            elif action == 'boost' and game_data['player']['boost'] >= 25:
                game_data['player']['speed'] += 1
                game_data['player']['boost'] -= 25

            # Update player position
            self._update_game_state(game_data)

            # Check for collisions
            self._check_collisions(game_data)

            # Check if player reached the finish line
            if game_data['player']['distance'] >= game_data['track']['length']:
                game_data['game_state']['game_over'] = True
                game_data['game_state']['win'] = True

                # Calculate final score based on time, lives, and distance
                time_bonus = max(0, 300 - game_data['game_state']['time']) * 2
                lives_bonus = game_data['player']['lives'] * 100
                final_score = time_bonus + lives_bonus + 500  # Base score for finishing

                game_data['game_state']['score'] = final_score

                # Update the score in the score manager
                self.game_manager.score_manager.update_score(
                    user_id,
                    score_increment=min(final_score, 1000),
                    stat_updates={'company': 1},
                )

            # Check if player lost all lives
            if game_data['player']['lives'] <= 0:
                game_data['game_state']['game_over'] = True
                game_data['game_state']['win'] = False

                # Calculate partial score based on distance traveled
                distance_percentage = game_data['player']['distance'] / game_data['track']['length']
                partial_score = int(distance_percentage * 500)  # Up to 500 points for distance

                game_data['game_state']['score'] = partial_score

                # Update the score in the score manager (partial credit)
                self.game_manager.score_manager.update_score(
                    user_id,
                    score_increment=partial_score,
                )

            # Update the game data
            self.game_manager.update_game_data(data_id, game_data)

    def _update_game_state(self, game_data: Dict[str, Any]) -> None:
        """
        Update the game state based on player speed and other factors.

        Args:
            game_data: The current game data
        """
        # Update distance based on speed
        game_data['player']['distance'] += game_data['player']['speed']

        # Update current segment
        game_data['track']['current_segment'] = min(
            int(game_data['player']['distance'] / 10),  # Each segment is 10 units
            int(game_data['track']['length'] / 10)
        )

        # Gradually increase speed if not at max
        if game_data['player']['speed'] < 5 and random.random() < 0.05:
            game_data['player']['speed'] += 0.1

        # Gradually increase boost meter
        if game_data['player']['boost'] < 100:
            game_data['player']['boost'] += 0.5

        # Update time (each update is roughly 0.1 seconds in game time)
        game_data['game_state']['time'] += 0.1

    def _check_collisions(self, game_data: Dict[str, Any]) -> None:
        """
        Check for collisions with obstacles and power-ups.

        Args:
            game_data: The current game data
        """
        player_position = game_data['player']['position']
        player_distance = game_data['player']['distance']

        # Check for obstacle collisions
        for obstacle in game_data['track']['obstacles']:
            if not obstacle.get('hit', False):  # Only check obstacles that haven't been hit
                # Check if player is at the obstacle's position
                if abs(obstacle['position'] * 10 - player_distance) < 5:  # Within collision range
                    if obstacle['lane'] == player_position:
                        # Collision with obstacle
                        obstacle['hit'] = True
                        game_data['player']['lives'] -= 1
                        game_data['player']['speed'] = max(1, game_data['player']['speed'] - 1)  # Reduce speed
                        break

        # Check for power-up collisions
        for power_up in game_data['track']['power_ups']:
            if not power_up.get('collected', False):  # Only check power-ups that haven't been collected
                # Check if player is at the power-up's position
                if abs(power_up['position'] * 10 - player_distance) < 5:  # Within collection range
                    if power_up['lane'] == player_position:
                        # Collect power-up
                        power_up['collected'] = True

                        # Apply power-up effect
                        if power_up['type'] == 'boost':
                            game_data['player']['boost'] = min(100, game_data['player']['boost'] + 50)
                        elif power_up['type'] == 'life':
                            game_data['player']['lives'] += 1
                        elif power_up['type'] == 'speed':
                            game_data['player']['speed'] = min(5, game_data['player']['speed'] + 0.5)
                        break

    def _generate_obstacles(self, track_length: int) -> List[Dict[str, Any]]:
        """
        Generate obstacles for the track.

        Args:
            track_length: Length of the track

        Returns:
            List of obstacle dictionaries
        """
        obstacles = []

        # Number of obstacles scales with track length
        num_obstacles = int(track_length / 20)  # One obstacle every ~20 units on average

        # Generate obstacles with increasing frequency
        for i in range(num_obstacles):
            # Position obstacles along the track, with more towards the end
            position_factor = i / num_obstacles  # 0 to 1
            min_position = int(position_factor * track_length * 0.1)  # Start after 10% of track
            max_position = int(min(position_factor * track_length * 1.5, track_length - 50))  # End before finish

            position = random.randint(min_position, max_position)
            lane = random.randint(0, 4)  # 5 lanes (0-4)

            # Different types of obstacles
            obstacle_types = ['rock', 'oil', 'cone', 'barrier']
            obstacle_type = random.choice(obstacle_types)

            obstacles.append({
                'position': position // 10,  # Convert to segment position
                'lane': lane,
                'type': obstacle_type,
                'hit': False
            })

        return obstacles

    def _generate_power_ups(self, track_length: int) -> List[Dict[str, Any]]:
        """
        Generate power-ups for the track.

        Args:
            track_length: Length of the track

        Returns:
            List of power-up dictionaries
        """
        power_ups = []

        # Number of power-ups scales with track length
        num_power_ups = int(track_length / 40)  # One power-up every ~40 units on average

        # Generate power-ups
        for i in range(num_power_ups):
            # Distribute power-ups evenly along the track
            position = random.randint(int(track_length * 0.1), int(track_length * 0.9))
            lane = random.randint(0, 4)  # 5 lanes (0-4)

            # Different types of power-ups
            power_up_types = ['boost', 'life', 'speed']
            weights = [0.6, 0.2, 0.2]  # More boost power-ups
            power_up_type = random.choices(power_up_types, weights=weights, k=1)[0]

            power_ups.append({
                'position': position // 10,  # Convert to segment position
                'lane': lane,
                'type': power_up_type,
                'collected': False
            })

        return power_ups
