# routes/card_game_routes.py
import logging

from flask import Blueprint, jsonify, request

from models.card_game_mode import CardGameMode

card_game_bp = Blueprint('card_game', __name__, url_prefix='/api/card_game')

def init_card_game_routes(card_game_mode: CardGameMode):
    """
    Initialize routes for the card game mode.

    Args:
        card_game_mode: CardGameMode instance
    """
    @card_game_bp.route('/get_state', methods=['GET'])
    def get_state():
        """
        Get the current game state.

        Query Parameters:
            data_id: ID of the game data
        """
        try:
            data_id = int(request.args.get('data_id', 0))

            # Get the game state
            result = card_game_mode.get_question_data(data_id, [], 0)

            return jsonify(result)
        except Exception as e:
            logging.error(f"Error getting game state: {e}")
            return jsonify({"error": str(e)})
    @card_game_bp.route('/play_card', methods=['POST'])
    def play_card():
        """
        Play a card from the player's hand to the board.

        Query Parameters:
            data_id: ID of the game data
            card_index: Index of the card in the player's hand
            board_position: Position on the board to place the card
        """
        try:
            data_id = int(request.args.get('data_id', 0))
            card_index = int(request.args.get('card_index', 0))
            board_position = int(request.args.get('board_position', 0))

            # Play the card
            result = card_game_mode.play_card(data_id, card_index, board_position)

            return jsonify(result)
        except Exception as e:
            logging.error(f"Error playing card: {e}")
            return jsonify({"error": str(e)})

    @card_game_bp.route('/draw_card', methods=['POST'])
    def draw_card():
        """
        Draw a card from the player's deck.

        Query Parameters:
            data_id: ID of the game data
        """
        try:
            data_id = int(request.args.get('data_id', 0))

            # Get the game state
            game_state = card_game_mode.game_manager.get_game_data(data_id)
            if game_state is None or game_state["game_over"]:
                return jsonify({"error": "Game not found or already over"})

            # Check if it's player's turn
            if game_state["current_turn"] != "player":
                return jsonify({"error": "Not your turn"})

            # Check if player has cards in deck
            if not game_state["player_deck"]:
                return jsonify({"error": "No cards left in deck"})

            # Check if player's hand is full
            max_hand_size = card_game_mode.card_data["game_rules"]["max_hand_size"]
            if len(game_state["player_hand"]) >= max_hand_size:
                return jsonify({"error": "Hand is full"})

            # Draw a card
            card_id = game_state["player_deck"].pop(0)
            game_state["player_hand"].append(card_id)

            # Update game state
            card_game_mode.game_manager.update_game_data(data_id, game_state)

            # Return updated game state
            result = card_game_mode.get_question_data(data_id, [], game_state["turn_number"])

            return jsonify(result)
        except Exception as e:
            logging.error(f"Error drawing card: {e}")
            return jsonify({"error": str(e)})

    @card_game_bp.route('/end_turn', methods=['POST'])
    def end_turn():
        """
        End the player's turn and let the AI play.

        Query Parameters:
            data_id: ID of the game data
        """
        try:
            data_id = int(request.args.get('data_id', 0))

            # End the turn
            result = card_game_mode.end_turn(data_id)

            return jsonify(result)
        except Exception as e:
            logging.error(f"Error ending turn: {e}")
            return jsonify({"error": str(e)})

def register_card_game_blueprint(app, card_game_mode: CardGameMode):
    """
    Register the card game blueprint with the Flask app.

    Args:
        app: Flask application instance
        card_game_mode: CardGameMode instance
    """
    init_card_game_routes(card_game_mode)
    app.register_blueprint(card_game_bp)
