# routes/card_game_routes.py
import logging

from flask import Blueprint, jsonify, request

from models.dataset_registry import DatasetRegistry


def init_card_game_routes(registry: DatasetRegistry) -> Blueprint:
    card_game_bp = Blueprint('card_game', __name__, url_prefix='/api/card_game')

    def _card_mode():
        ds = registry.current(request)
        return ds.card_game_mode if ds else None

    @card_game_bp.route('/get_state', methods=['GET'])
    def get_state():
        card_game_mode = _card_mode()
        if card_game_mode is None:
            return jsonify({'error': 'No dataset configured'}), 503
        try:
            data_id = int(request.args.get('data_id', 0))
            result = card_game_mode.get_question_data(data_id, [], 0)
            return jsonify(result)
        except Exception as e:
            logging.error(f'Error getting game state: {e}')
            return jsonify({'error': str(e)})

    @card_game_bp.route('/play_card', methods=['POST'])
    def play_card():
        card_game_mode = _card_mode()
        if card_game_mode is None:
            return jsonify({'error': 'No dataset configured'}), 503
        try:
            data_id = int(request.args.get('data_id', 0))
            card_index = int(request.args.get('card_index', 0))
            board_position = int(request.args.get('board_position', 0))
            result = card_game_mode.play_card(data_id, card_index, board_position)
            return jsonify(result)
        except Exception as e:
            logging.error(f'Error playing card: {e}')
            return jsonify({'error': str(e)})

    @card_game_bp.route('/draw_card', methods=['POST'])
    def draw_card():
        card_game_mode = _card_mode()
        if card_game_mode is None:
            return jsonify({'error': 'No dataset configured'}), 503
        try:
            data_id = int(request.args.get('data_id', 0))

            game_state = card_game_mode.game_manager.get_game_data(data_id)
            if game_state is None or game_state['game_over']:
                return jsonify({'error': 'Game not found or already over'})

            if game_state['current_turn'] != 'player':
                return jsonify({'error': 'Not your turn'})

            if not game_state['player_deck']:
                return jsonify({'error': 'No cards left in deck'})

            max_hand_size = card_game_mode.card_data['game_rules']['max_hand_size']
            if len(game_state['player_hand']) >= max_hand_size:
                return jsonify({'error': 'Hand is full'})

            card_id = game_state['player_deck'].pop(0)
            game_state['player_hand'].append(card_id)
            card_game_mode.game_manager.update_game_data(data_id, game_state)

            result = card_game_mode.get_question_data(data_id, [], game_state['turn_number'])
            return jsonify(result)
        except Exception as e:
            logging.error(f'Error drawing card: {e}')
            return jsonify({'error': str(e)})

    @card_game_bp.route('/end_turn', methods=['POST'])
    def end_turn():
        card_game_mode = _card_mode()
        if card_game_mode is None:
            return jsonify({'error': 'No dataset configured'}), 503
        try:
            data_id = int(request.args.get('data_id', 0))
            result = card_game_mode.end_turn(data_id)
            return jsonify(result)
        except Exception as e:
            logging.error(f'Error ending turn: {e}')
            return jsonify({'error': str(e)})


    return card_game_bp


def register_card_game_blueprint(app, registry: DatasetRegistry):
    card_game_bp = init_card_game_routes(registry)
    app.register_blueprint(card_game_bp)
