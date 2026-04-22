import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, make_response, redirect, request, send_from_directory, session
from flask_babel import Babel

from models.config import AppConfig
from models.dataset_registry import DATASET_COOKIE, DatasetRegistry
from routes.admin_routes import admin_bp
from routes.game_routes import init_routes

load_dotenv()
logging.basicConfig(level=logging.INFO)

# Paths the user can still reach when no dataset is configured yet (first-run).
_FIRST_RUN_ALLOWED_PREFIXES = ('/setup', '/static/', '/lang/')


def create_app(config_path: str | None = None):
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['fr', 'en']

    def get_locale():
        return request.cookies.get('lang', 'fr')

    Babel(app, locale_selector=get_locale)

    config_file = config_path or os.environ.get('APP_CONFIG', 'config.yaml')
    app.config['CONFIG_PATH'] = config_file

    try:
        app_config = AppConfig(config_file)
    except FileNotFoundError:
        app_config = None

    registry = (
        DatasetRegistry.from_app_config(app_config)
        if app_config is not None
        else DatasetRegistry()
    )
    app.config['DATASET_REGISTRY'] = registry
    app.config['APP_CONFIG_OBJECT'] = app_config

    game_bp = init_routes(registry)

    app.register_blueprint(game_bp)
    app.register_blueprint(admin_bp)

    @app.before_request
    def _redirect_to_setup_when_empty():
        if not registry.is_empty():
            return None
        path = request.path
        if any(path == p.rstrip('/') or path.startswith(p) for p in _FIRST_RUN_ALLOWED_PREFIXES):
            return None
        return redirect('/setup')

    @app.context_processor
    def inject_globals():
        ds = registry.current(request)
        contact_email = app.config['APP_CONFIG_OBJECT'].contact_email if app.config.get('APP_CONFIG_OBJECT') else ''
        datasets_list = [
            {'id': d.id, 'name': d.config.company_name}
            for d in registry.values()
        ]
        if ds is None:
            return {
                'company_name': 'My Company',
                'company_logo_url': '',
                'company_tagline': '',
                'company_email': contact_email,
                'current_lang': get_locale(),
                'datasets': datasets_list,
                'current_dataset_id': '',
            }
        return {
            'company_name': ds.config.company_name,
            'company_logo_url': ds.config.logo_url,
            'company_tagline': ds.config.tagline,
            'company_email': contact_email,
            'current_lang': get_locale(),
            'datasets': datasets_list,
            'current_dataset_id': ds.id,
        }

    @app.route('/favicon.ico')
    def favicon():
        # Browsers still request /favicon.ico even with <link rel="icon">.
        # Return an empty 204 to keep the access log clean.
        return ('', 204)

    @app.route('/photos/<path:filename>')
    def serve_photo(filename):
        ds = registry.current(request)
        if ds is None:
            abort(404)
        photos_dir = Path(ds.config.images_dir).resolve()
        return send_from_directory(photos_dir, filename)

    @app.route('/lang/<lang_code>')
    def set_language(lang_code):
        resp = make_response(redirect(request.referrer or '/'))
        if lang_code in app.config['BABEL_SUPPORTED_LOCALES']:
            resp.set_cookie('lang', lang_code, max_age=365 * 24 * 3600)
        return resp

    @app.route('/dataset/<dataset_id>')
    def set_dataset(dataset_id):
        # Unknown id → ignore, don't set cookie
        if registry.get(dataset_id) is None:
            return redirect(request.referrer or '/')
        resp = make_response(redirect(request.referrer or '/'))
        resp.set_cookie(DATASET_COOKIE, dataset_id, max_age=365 * 24 * 3600)
        # Switching datasets invalidates any in-progress game
        session.clear()
        return resp

    return app


def _get_app():
    return create_app()


app = _get_app()

if __name__ == '__main__':
    if app is None:
        raise SystemExit('Cannot start: failed to create Flask app.')
    app.run(
        host=os.environ.get('FLASK_HOST', '127.0.0.1'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true',
    )
