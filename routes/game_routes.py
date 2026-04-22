# routes/game_routes.py
import logging

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from models.dataset_registry import DatasetRegistry

EXPERIMENTAL_MODES = {
    'speed', 'team_guess', 'missing_person', 'position_match', 'progressive_hint',
    'scrambled_face', 'emoji_challenge', 'silhouette', 'mirror', 'card_game',
}


def init_routes(registry: DatasetRegistry) -> Blueprint:
    game_bp = Blueprint('game', __name__)

    def _current():
        return registry.current(request)

    @game_bp.route('/')
    def index():
        ds = _current()
        if ds is None:
            return redirect('/setup')
        modes = ds.mode_factory.get_all_modes()

        regular_modes = []
        experimental_mode_info = []
        for mode in modes.values():
            if mode.name == 'arr':
                continue
            mode_data = {'name': mode.name, 'description': mode.description}
            if mode.name in EXPERIMENTAL_MODES:
                experimental_mode_info.append(mode_data)
            else:
                regular_modes.append(mode_data)

        return render_template(
            'mode_selection.html',
            modes=regular_modes,
            experimental_modes=experimental_mode_info,
        )

    @game_bp.route('/mode_selection')
    def mode_selection():
        return index()

    @game_bp.route('/mode/<mode_name>')
    def start_mode(mode_name):
        ds = _current()
        if ds is None:
            return redirect('/setup')

        logging.info(f'Mode {mode_name} selected')

        mode = ds.mode_factory.get_mode(mode_name)
        if mode is None:
            logging.error(f'Game mode {mode_name} not found')
            return redirect(url_for('game.index'))

        user_id = session.get('user_id')
        game_data = mode.initialize(user_id)

        session['user_id'] = game_data['user_id']
        session['data_id'] = game_data['data_id']
        session['max_score'] = game_data.get('max_score', 0)
        session['all_indices'] = []
        session['used_indices'] = []
        session['current_question'] = 0
        session['mode_name'] = mode_name
        session['dataset_id'] = ds.id

        return redirect(url_for('game.question'))

    @game_bp.route('/question')
    def question():
        ds = _current()
        if ds is None:
            return redirect('/setup')

        if 'data_id' not in session:
            logging.error('Game not initialized')
            return redirect(url_for('game.index'))

        mode_name = session.get('mode_name', 'normal')
        mode = ds.mode_factory.get_mode(mode_name)
        if mode is None:
            logging.error(f'Game mode {mode_name} not found')
            return redirect(url_for('game.index'))

        session.setdefault('all_indices', [])
        session.setdefault('used_indices', [])
        session.setdefault('current_question', 0)

        question_data = mode.get_question_data(
            session['data_id'],
            session['used_indices'],
            session['current_question'],
        )

        if question_data.get('game_over', False):
            return redirect(url_for('game.result'))

        session['current_question'] = question_data.get('current_question', session['current_question'])
        session.modified = True

        user_id = session.get('user_id')
        user_score = ds.score_manager.get_user_score(user_id)
        stats = ds.score_manager.get_stats(user_id)

        template_data = {
            'maxScore': session.get('max_score', 0),
            'stats': stats,
            'currentScore': user_score['score'],
            'best_score': user_score.get('best_score', 0),
            'total_questions': len(ds.game_manager.get_game_data(session['data_id'])),
            'current_question': session.get('current_question', 0),
            'total_employees': len(ds.game_manager.get_game_data(session['data_id'])),
            'use_normal_mode_styles': mode_name == 'normal',
            'use_score_section_styles': True,
        }
        template_data.update(question_data)

        return render_template(mode.template, **template_data)

    @game_bp.route('/check', methods=['POST'])
    def check():
        ds = _current()
        if ds is None:
            return redirect('/setup')

        if 'data_id' not in session:
            logging.error('Game not initialized')
            return redirect(url_for('game.index'))

        mode_name = session.get('mode_name', 'normal')
        mode = ds.mode_factory.get_mode(mode_name)
        if mode is None:
            logging.error(f'Game mode {mode_name} not found')
            return redirect(url_for('game.index'))

        user_id = session.get('user_id')
        session_updates = mode.handle_answer(user_id, request.form, session)
        if session_updates:
            session.update(session_updates)
            session.modified = True

        return redirect(url_for('game.question'))

    @game_bp.route('/result')
    def result():
        ds = _current()
        if ds is None:
            return redirect('/setup')

        if 'data_id' not in session:
            logging.error('Game not initialized')
            return redirect(url_for('game.index'))

        mode_name = session.get('mode_name', 'normal')
        mode = ds.mode_factory.get_mode(mode_name)
        if mode is None:
            logging.error(f'Game mode {mode_name} not found')
            return redirect(url_for('game.index'))

        user_id = session.get('user_id')
        max_score = session.get('max_score', 0)
        total_questions = len(session.get('used_indices', []))

        result_data = ds.game_manager.get_result_data(user_id, max_score, total_questions)

        return render_template('result.html', **result_data)

    @game_bp.route('/restart')
    def restart():
        session.clear()
        return redirect(url_for('game.index'))

    @game_bp.route('/arr')
    def arr_easter_egg():
        return render_template('arr.html')

    @game_bp.route('/api/employee_images')
    def get_employee_images():
        ds = _current()
        if ds is None:
            return jsonify([])
        employees = ds.employee_data.get_all_employees()
        return jsonify([emp['photo'] for emp in employees])

    @game_bp.route('/about')
    def about():
        return render_template('about.html')

    @game_bp.route('/how-to-play')
    def how_to_play():
        return render_template('how_to_play.html')

    @game_bp.route('/scores')
    def scores_page():
        ds = _current()
        if ds is None:
            return redirect('/setup')
        score_manager = ds.score_manager

        top_scores = {
            'normal': score_manager.get_top_scores('normal', 5),
            'reverse': score_manager.get_top_scores('reverse', 5),
            'pixelation': score_manager.get_top_scores('pixelation', 5),
            'timed': score_manager.get_top_scores('timed', 5),
        }

        return render_template(
            'scores.html',
            top_scores=top_scores,
            total_players=score_manager.get_total_players(),
            total_games=score_manager.get_total_games(),
            average_score=score_manager.get_average_score(),
            highest_score=score_manager.get_highest_score(),
        )

    return game_bp
