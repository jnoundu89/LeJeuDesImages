# routes/game_routes.py
import logging
import random
from typing import cast

from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_babel import gettext as _

from models.dataset_registry import DatasetRegistry


def _tag_label(tag: str) -> str:
    """Translate a mode tag to its display label.

    Tags are stored on GameMode subclasses as lowercase French keys
    (``'rapide'``, ``'culture'``, …) so they serve both as i18n
    identifiers and as stable JS-side filter keys. The labels below
    are what the player sees in the filter bar and on each card.
    """
    # Inline dict so `pybabel extract` picks up the gettext calls.
    mapping = {
        'rapide': _('Rapide'),
        'culture': _('Culture'),
        'photo': _('Photo'),
        'devinette': _('Devinette'),
        'memoire': _('Mémoire'),
        'nouveau': _('Nouveau'),
        'populaire': _('Populaire'),
        'temps': _('Temps'),
        'experimental': _('Expérimental'),
    }
    return mapping.get(tag, tag)


def _mode_view_data(mode) -> dict:
    """Pack a GameMode instance into a plain dict for Jinja.

    Keeps the template dumb: no ``if/elif mode.name == ...`` branches
    anywhere — everything comes from ``mode.<declared attribute>``.
    """
    availability = mode.is_available()
    # Expose tags as a list of {key, label} pairs so templates can filter
    # on the stable key while displaying the translated label.
    tag_objects = [{'key': t, 'label': _tag_label(t)} for t in mode.tags]
    return {
        'name': mode.name,
        'display_name': mode.display_name,
        'description': mode.description,
        'icon': mode.icon,
        'preview_type': mode.preview_type,
        'tags': list(mode.tags),
        'tag_objects': tag_objects,
        'difficulty': mode.difficulty,
        'estimated_duration_sec': mode.estimated_duration_sec,
        'experimental': mode.experimental,
        'available': availability.available,
        'missing_fields': availability.missing_fields,
        'required_fields': availability.required_fields,
        'eligible_count': availability.eligible_count,
        'min_eligible': availability.min_eligible,
    }


def _current_user_id() -> int | None:
    """Return the int user_id stored on the Flask session, or None if missing."""
    raw = session.get('user_id')
    return int(raw) if raw is not None else None


def init_routes(registry: DatasetRegistry) -> Blueprint:
    game_bp = Blueprint('game', __name__)

    def _current():
        return registry.current(request)

    @game_bp.route('/')
    def index():
        ds = _current()
        if ds is None:
            return redirect('/setup')

        modes = [_mode_view_data(m) for m in ds.mode_factory.get_all_modes().values()]
        # Stable-sort: available first, then by difficulty asc, then by name
        modes.sort(key=lambda m: (not m['available'], m['difficulty'], str(m['display_name'])))

        tag_keys = sorted({tag for m in modes for tag in m['tags']})
        all_tags = [{'key': t, 'label': _tag_label(t)} for t in tag_keys]

        return render_template(
            'mode_selection.html',
            modes=modes,
            all_tags=all_tags,
            available_count=sum(1 for m in modes if m['available']),
            hide_unavailable_modes=ds.config.hide_unavailable_modes,
        )

    @game_bp.route('/mode_selection')
    def mode_selection():
        return index()

    @game_bp.route('/mode/random')
    def random_mode():
        ds = _current()
        if ds is None:
            return redirect('/setup')
        available = [m for m in ds.mode_factory.get_all_modes().values() if m.is_available().available]
        if not available:
            return redirect(url_for('game.index'))
        pick = random.choice(available)
        return redirect(url_for('game.start_mode', mode_name=pick.name))

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

        user_id = _current_user_id()
        if user_id is None:
            logging.error('Game session missing user_id; restarting')
            return redirect(url_for('game.index'))
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

        user_id = _current_user_id()
        if user_id is None:
            logging.error('Game session missing user_id; restarting')
            return redirect(url_for('game.index'))
        # Flask's SessionMixin is dict-compatible at runtime; cast to satisfy
        # the handler's strict `dict` annotation.
        session_updates = mode.handle_answer(user_id, request.form, cast(dict, session))
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

        user_id = _current_user_id()
        if user_id is None:
            logging.error('Game session missing user_id; restarting')
            return redirect(url_for('game.index'))
        max_score = session.get('max_score', 0)
        total_questions = len(session.get('used_indices', []))

        result_data = ds.game_manager.get_result_data(user_id, max_score, total_questions)

        return render_template('result.html', **result_data)

    @game_bp.route('/restart')
    def restart():
        session.clear()
        return redirect(url_for('game.index'))

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

        mode_list = []
        top_scores = {}
        for mode in ds.mode_factory.get_all_modes().values():
            top_scores[mode.name] = score_manager.get_top_scores(mode.name, 5)
            mode_list.append({'name': mode.name, 'display_name': mode.display_name})
        mode_list.sort(key=lambda m: str(m['display_name']))

        return render_template(
            'scores.html',
            modes=mode_list,
            top_scores=top_scores,
            total_players=score_manager.get_total_players(),
            total_games=score_manager.get_total_games(),
            average_score=score_manager.get_average_score(),
            highest_score=score_manager.get_highest_score(),
        )

    return game_bp
