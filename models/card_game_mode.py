# models/card_game_mode.py
import json
import os
import random
from typing import Any, Dict, List, Optional

from flask_babel import lazy_gettext as _l

from .game_mode import GameMode


class CardGameMode(GameMode):
    """
    Card game mode where players battle against an AI opponent using cards with different stats and abilities.
    This mode is inspired by games like Hearthstone, Slay the Spire, and Triple Triad.
    """
    @property
    def name(self) -> str:
        return "card_game"

    @property
    def description(self) -> str:
        return _l("Mode Jeu de Cartes : Affrontez l'IA dans un duel de cartes stratégique")

    @property
    def template(self) -> str:
        return "card_game.html"

    def __init__(self, game_manager):
        """
        Initialize the card game mode.

        Args:
            game_manager: GameManager instance for managing the game
        """
        super().__init__(game_manager)
        self.card_data_path = os.path.join('static', 'data', 'card_game_data.json')
        self._load_card_data()

    def _load_card_data(self):
        """Load card data from JSON file."""
        try:
            with open(self.card_data_path, 'r', encoding='utf-8') as f:
                self.card_data = json.load(f)
        except Exception as e:
            print(f"Error loading card data: {e}")
            # Initialize with empty data if file can't be loaded
            self.card_data = {"cards": [], "ai_decks": [], "game_rules": {}}

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialize the card game mode.

        Args:
            user_id: Optional user ID. If not provided, a new user will be created.

        Returns:
            Dictionary with game initialization data
        """
        # Initialize user
        user_id = self.game_manager.score_manager.initialize_user(user_id)

        # Select difficulty (default to medium)
        difficulty = "medium"

        # Get AI deck for selected difficulty
        ai_deck = next((deck for deck in self.card_data["ai_decks"]
                        if deck["difficulty"] == difficulty),
                       self.card_data["ai_decks"][0])

        # Get all cards
        all_cards = self.card_data["cards"]

        # Create player deck (random selection of cards)
        available_card_ids = [card["id"] for card in all_cards]
        player_card_ids = random.sample(available_card_ids, 8)  # 8 cards in deck

        # Get game rules
        game_rules = self.card_data["game_rules"]

        # Initialize game state
        game_state = {
            "player_health": game_rules["starting_health"],
            "ai_health": game_rules["starting_health"],
            "player_mana": game_rules["starting_mana"],
            "ai_mana": game_rules["starting_mana"],
            "player_deck": player_card_ids,
            "ai_deck": ai_deck["cards"],
            "player_hand": [],
            "ai_hand": [],
            "player_board": [],
            "ai_board": [],
            "current_turn": "player",
            "turn_number": 1,
            "game_over": False,
            "winner": None,
            "difficulty": difficulty,
            "ai_strategy": ai_deck["strategy"]
        }

        # Draw initial hands
        for _ in range(game_rules["starting_hand"]):
            if game_state["player_deck"]:
                card_id = game_state["player_deck"].pop(0)
                game_state["player_hand"].append(card_id)

            if game_state["ai_deck"]:
                card_id = game_state["ai_deck"].pop(0)
                game_state["ai_hand"].append(card_id)

        # Store game state
        data_id = self.game_manager.store_game_data(game_state)

        # Return initialization data
        return {
            "user_id": user_id,
            "data_id": data_id,
            "max_score": 100,  # Maximum possible score
            "difficulty": difficulty
        }

    def get_question_data(self, data_id: int, used_indices: List[int],
                         current_question: int) -> Dict[str, Any]:
        """
        Get data for the current game state.

        Args:
            data_id: ID of the game data
            used_indices: List of indices that have already been used
            current_question: Current question number

        Returns:
            Dictionary with game state data
        """
        # Get the game state
        game_state = self.game_manager.get_game_data(data_id)
        if game_state is None:
            return {"game_over": True}

        # Get all cards data
        all_cards = {card["id"]: card for card in self.card_data["cards"]}

        # Prepare player hand data with full card details
        player_hand = [all_cards.get(card_id, {}) for card_id in game_state["player_hand"]]

        # Prepare player board data with full card details
        player_board = [all_cards.get(card_id, {}) for card_id in game_state["player_board"]]

        # Prepare AI board data with full card details
        ai_board = [all_cards.get(card_id, {}) for card_id in game_state["ai_board"]]

        # Count cards in AI hand (don't reveal the actual cards)
        ai_hand_count = len(game_state["ai_hand"])

        # Count cards left in decks
        player_deck_count = len(game_state["player_deck"])
        ai_deck_count = len(game_state["ai_deck"])

        # Return game state data
        return {
            "game_over": game_state["game_over"],
            "winner": game_state["winner"],
            "player_health": game_state["player_health"],
            "ai_health": game_state["ai_health"],
            "player_mana": game_state["player_mana"],
            "ai_mana": game_state["ai_mana"],
            "player_hand": player_hand,
            "player_board": player_board,
            "ai_board": ai_board,
            "ai_hand_count": ai_hand_count,
            "player_deck_count": player_deck_count,
            "ai_deck_count": ai_deck_count,
            "current_turn": game_state["current_turn"],
            "turn_number": game_state["turn_number"],
            "difficulty": game_state["difficulty"],
            "current_question": current_question,
            "game_rules": self.card_data["game_rules"]
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        """
        Update the score for this game mode.

        Args:
            user_id: The user ID
            **kwargs: Additional arguments specific to the game mode
        """
        # Get game result
        game_won = kwargs.get("game_won", False)
        ai_health_remaining = kwargs.get("ai_health_remaining", 30)
        player_health_remaining = kwargs.get("player_health_remaining", 0)
        turns_taken = kwargs.get("turns_taken", 0)
        difficulty = kwargs.get("difficulty", "medium")

        # Calculate score based on game result
        score = 0
        if game_won:
            # Base score for winning
            score += 50

            # Bonus for remaining health
            score += player_health_remaining

            # Bonus for quick victory
            if turns_taken <= 10:
                score += 20
            elif turns_taken <= 15:
                score += 10

            # Difficulty bonus
            if difficulty == "hard":
                score += 20
            elif difficulty == "medium":
                score += 10
        else:
            # Consolation points based on damage dealt
            damage_dealt = 30 - ai_health_remaining
            score += damage_dealt

        # Cap score at 100
        score = min(score, 100)

        # Update the score
        self.game_manager.score_manager.update_score(
            user_id,
            score_increment=score,
        )

    def play_card(self, data_id: int, card_index: int, board_position: int) -> Dict[str, Any]:
        """
        Play a card from the player's hand to the board.

        Args:
            data_id: ID of the game data
            card_index: Index of the card in the player's hand
            board_position: Position on the board to place the card

        Returns:
            Updated game state
        """
        # Get the game state
        game_state = self.game_manager.get_game_data(data_id)
        if game_state is None or game_state["game_over"]:
            return {"error": "Game not found or already over"}

        # Check if it's the player's turn
        if game_state["current_turn"] != "player":
            return {"error": "Not your turn"}

        # Check if card index is valid
        if card_index < 0 or card_index >= len(game_state["player_hand"]):
            return {"error": "Invalid card index"}

        # Check if board position is valid
        if board_position < 0 or board_position >= self.card_data["game_rules"]["board_size"]:
            return {"error": "Invalid board position"}

        # Check if board position is already occupied
        if len(game_state["player_board"]) > board_position and game_state["player_board"][board_position] is not None:
            return {"error": "Board position already occupied"}

        # Get the card
        card_id = game_state["player_hand"][card_index]
        card = next((c for c in self.card_data["cards"] if c["id"] == card_id), None)

        # Check if player has enough mana
        if card["mana_cost"] > game_state["player_mana"]:
            return {"error": "Not enough mana"}

        # Remove card from hand
        game_state["player_hand"].pop(card_index)

        # Add card to board
        # Ensure the board has enough positions
        while len(game_state["player_board"]) <= board_position:
            game_state["player_board"].append(None)

        game_state["player_board"][board_position] = card_id

        # Deduct mana
        game_state["player_mana"] -= card["mana_cost"]

        # Update game state
        self.game_manager.update_game_data(data_id, game_state)

        return self.get_question_data(data_id, [], game_state["turn_number"])

    def end_turn(self, data_id: int) -> Dict[str, Any]:
        """
        End the player's turn and let the AI play.

        Args:
            data_id: ID of the game data

        Returns:
            Updated game state
        """
        # Get the game state
        game_state = self.game_manager.get_game_data(data_id)
        if game_state is None or game_state["game_over"]:
            return {"error": "Game not found or already over"}

        # Check if it's the player's turn
        if game_state["current_turn"] != "player":
            return {"error": "Not your turn"}

        # Switch to AI turn
        game_state["current_turn"] = "ai"

        # AI plays its turn
        game_state = self._ai_turn(game_state)

        # Check for game over
        if game_state["player_health"] <= 0:
            game_state["game_over"] = True
            game_state["winner"] = "ai"
        elif game_state["ai_health"] <= 0:
            game_state["game_over"] = True
            game_state["winner"] = "player"

        # If game not over, start new turn
        if not game_state["game_over"]:
            # Switch back to player turn
            game_state["current_turn"] = "player"
            game_state["turn_number"] += 1

            # Increase mana for new turn (up to max)
            new_mana = min(game_state["turn_number"], self.card_data["game_rules"]["max_mana"])
            game_state["player_mana"] = new_mana
            game_state["ai_mana"] = new_mana

            # Draw a card for player
            if game_state["player_deck"] and len(game_state["player_hand"]) < self.card_data["game_rules"]["max_hand_size"]:
                card_id = game_state["player_deck"].pop(0)
                game_state["player_hand"].append(card_id)

            # Draw a card for AI
            if game_state["ai_deck"] and len(game_state["ai_hand"]) < self.card_data["game_rules"]["max_hand_size"]:
                card_id = game_state["ai_deck"].pop(0)
                game_state["ai_hand"].append(card_id)

        # Update game state
        self.game_manager.update_game_data(data_id, game_state)

        return self.get_question_data(data_id, [], game_state["turn_number"])

    def _ai_turn(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the AI's turn.

        Args:
            game_state: Current game state

        Returns:
            Updated game state
        """
        # Get all cards data
        all_cards = {card["id"]: card for card in self.card_data["cards"]}

        # AI strategy based on difficulty
        strategy = game_state["ai_strategy"]

        # Sort AI hand by mana cost
        ai_hand_with_details = [(i, all_cards.get(card_id, {}))
                               for i, card_id in enumerate(game_state["ai_hand"])]

        if strategy == "aggressive":
            # Sort by attack value (highest first)
            ai_hand_with_details.sort(key=lambda x: x[1].get("attack", 0), reverse=True)
        elif strategy == "balanced":
            # Sort by combined attack and defense
            ai_hand_with_details.sort(key=lambda x: x[1].get("attack", 0) + x[1].get("defense", 0), reverse=True)
        else:  # basic
            # Sort by mana cost (lowest first)
            ai_hand_with_details.sort(key=lambda x: x[1].get("mana_cost", 999))

        # Try to play cards
        for card_index, card in ai_hand_with_details:
            # Skip if not enough mana
            if card.get("mana_cost", 0) > game_state["ai_mana"]:
                continue

            # Find an empty spot on the board
            board_position = -1
            for i in range(self.card_data["game_rules"]["board_size"]):
                if i >= len(game_state["ai_board"]) or game_state["ai_board"][i] is None:
                    board_position = i
                    break

            # If found an empty spot, play the card
            if board_position != -1:
                # Remove card from hand
                card_id = game_state["ai_hand"].pop(card_index)

                # Add card to board
                while len(game_state["ai_board"]) <= board_position:
                    game_state["ai_board"].append(None)

                game_state["ai_board"][board_position] = card_id

                # Deduct mana
                game_state["ai_mana"] -= card.get("mana_cost", 0)

        # Battle phase - each card attacks
        self._resolve_combat(game_state, all_cards)

        return game_state

    def _resolve_combat(self, game_state: Dict[str, Any], all_cards: Dict[int, Dict[str, Any]]) -> None:
        """
        Resolve combat between cards on the board.

        Args:
            game_state: Current game state
            all_cards: Dictionary of all cards by ID
        """
        # AI cards attack player cards or player directly
        for i, card_id in enumerate(game_state["ai_board"]):
            if card_id is None:
                continue

            card = all_cards.get(card_id, {})
            attack_value = card.get("attack", 0)

            # Find opposing card
            if i < len(game_state["player_board"]) and game_state["player_board"][i] is not None:
                # Attack opposing card
                target_card_id = game_state["player_board"][i]
                target_card = all_cards.get(target_card_id, {})

                # Calculate damage
                damage = max(0, attack_value - target_card.get("defense", 0))

                # Apply damage
                target_card["health"] = target_card.get("health", 0) - damage

                # Remove card if destroyed
                if target_card["health"] <= 0:
                    game_state["player_board"][i] = None
            else:
                # Attack player directly
                game_state["player_health"] -= attack_value

        # Player cards attack AI cards or AI directly
        for i, card_id in enumerate(game_state["player_board"]):
            if card_id is None:
                continue

            card = all_cards.get(card_id, {})
            attack_value = card.get("attack", 0)

            # Find opposing card
            if i < len(game_state["ai_board"]) and game_state["ai_board"][i] is not None:
                # Attack opposing card
                target_card_id = game_state["ai_board"][i]
                target_card = all_cards.get(target_card_id, {})

                # Calculate damage
                damage = max(0, attack_value - target_card.get("defense", 0))

                # Apply damage
                target_card["health"] = target_card.get("health", 0) - damage

                # Remove card if destroyed
                if target_card["health"] <= 0:
                    game_state["ai_board"][i] = None
            else:
                # Attack AI directly
                game_state["ai_health"] -= attack_value
