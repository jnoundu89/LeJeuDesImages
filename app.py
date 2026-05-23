import hashlib
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, make_response, redirect, request, send_from_directory, session, url_for
from flask_babel import Babel
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models.config import AppConfig
from models.dataset_registry import DATASET_COOKIE, DatasetRegistry
from routes.admin_routes import admin_bp
from routes.game_routes import init_routes

# Headers set on every HTML response to harden the browser sandbox.
# See https://owasp.org/www-project-secure-headers/ for the rationale.
_SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'same-origin',
    'Permissions-Policy': 'accelerometer=(), camera=(), geolocation=(), gyroscope=(), microphone=(), payment=()',
}
# Allow Alpine.js + Font Awesome + the Inter font from rsms.me; everything
# else stays same-origin. Alpine needs both `'unsafe-inline'` (for the
# <script> blocks emitted by mode templates + its own CDN script) AND
# `'unsafe-eval'` — internally it compiles every `x-data` / `x-show` /
# `@click` expression via `new Function()`, which CSP treats as eval.
# Without unsafe-eval, filter bar, mode cards, game timer and answer
# checking all silently break.
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://rsms.me https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
    "font-src 'self' https://rsms.me https://cdnjs.cloudflare.com https://fonts.gstatic.com data:; "
    "img-src 'self' data: https:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'"
)

load_dotenv()
logging.basicConfig(level=logging.INFO)

# Paths the user can still reach when no dataset is configured yet (first-run).
_FIRST_RUN_ALLOWED_PREFIXES = ('/setup', '/static/', '/lang/')


def create_app(config_path: str | None = None):
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
    # Default locale + supported set read from env so a new translation
    # (Spanish, German, …) only needs the catalogue + an env update,
    # no code change. Format: BABEL_SUPPORTED_LOCALES="fr,en,es".
    default_locale = os.environ.get('BABEL_DEFAULT_LOCALE', 'fr')
    supported_csv = os.environ.get('BABEL_SUPPORTED_LOCALES', 'fr,en')
    supported_locales = [code.strip() for code in supported_csv.split(',') if code.strip()]
    app.config['BABEL_DEFAULT_LOCALE'] = default_locale
    app.config['BABEL_SUPPORTED_LOCALES'] = supported_locales

    def get_locale():
        candidate = request.cookies.get('lang', default_locale)
        # Fall back to the default if the cookie carries an unknown code
        # (e.g. a new deploy narrowed the supported list).
        return candidate if candidate in supported_locales else default_locale

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

    # Rate-limit the admin login to slow down brute-force attempts.
    # In-memory backend is fine for single-process dev; switch to redis
    # via RATELIMIT_STORAGE_URI env for multi-worker deploys.
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[],  # opt-in per-route below
        storage_uri=os.environ.get('RATELIMIT_STORAGE_URI', 'memory://'),
        headers_enabled=True,
        enabled=not app.config.get('TESTING', False),
    )
    app.config['LIMITER'] = limiter

    game_bp = init_routes(registry)

    app.register_blueprint(game_bp)
    app.register_blueprint(admin_bp)

    # Apply the rate limit on the login endpoint itself once the blueprint
    # is registered (the decorator needs to resolve by name).
    limiter.limit('10 per 15 minutes', methods=['POST'])(
        app.view_functions['admin.setup_login']
    )
    # Tighter limit on mutating admin routes: enough for legitimate bulk
    # work (importing 50 employees in a row) but not enough to abuse.
    _mutation_endpoints = [
        'admin.save',
        'admin.delete',
        'admin.upload_csv',
        'admin.upload_photos',
        'admin.replace_csv',
        'admin.employee_create',
        'admin.employee_update',
        'admin.employee_delete',
        'admin.employee_upload_photo',
        'admin.cleanup_orphan_photos',
        'admin.import_dataset',
    ]
    for ep in _mutation_endpoints:
        view = app.view_functions.get(ep)
        if view is not None:
            limiter.limit('60 per minute')(view)

    # Cache buster: append ?v=<hash8> to static URLs based on content.
    # Computed lazily, cached in-process — O(1) after the first hit per file.
    _static_version_cache: dict[str, str] = {}

    def _static_version(filename: str) -> str:
        if filename in _static_version_cache:
            return _static_version_cache[filename]
        path = Path(app.static_folder or 'static') / filename
        try:
            h = hashlib.blake2b(path.read_bytes(), digest_size=4).hexdigest()
        except OSError:
            h = '0'
        _static_version_cache[filename] = h
        return h

    @app.template_global('static_v')
    def static_v(filename: str) -> str:
        """Return a URL for a static file with a content-hash cache buster."""
        return f"{url_for('static', filename=filename)}?v={_static_version(filename)}"

    @app.after_request
    def _apply_security_headers(response):
        # Only set headers on HTML responses; skip binary assets.
        content_type = response.content_type or ''
        if 'text/html' in content_type:
            for key, value in _SECURITY_HEADERS.items():
                response.headers.setdefault(key, value)
            response.headers.setdefault('Content-Security-Policy', _CSP)
        return response

    @app.before_request
    def _redirect_to_setup_when_empty():
        if not registry.is_empty():
            return None
        path = request.path
        if any(path == p.rstrip('/') or path.startswith(p) for p in _FIRST_RUN_ALLOWED_PREFIXES):
            return None
        return redirect('/setup')

    def _theme_inline_style(theme) -> str:
        """Build the ``style="--token: hex; ..."`` payload for <html>.

        Every token the admin has overridden becomes a CSS custom
        property at document root, beating the palette rule from
        design-tokens.css (inline > any stylesheet). Empty string when
        nothing is overridden — palette defaults are enough then.
        Values are already hex-validated by DatasetTheme so the string
        is safe to emit raw.
        """
        parts = [f'--{token}: {value}' for token, value in theme.resolved_overrides().items()]
        return '; '.join(parts) + (';' if parts else '')

    @app.context_processor
    def inject_globals():
        ds = registry.current(request)
        contact_email = app.config['APP_CONFIG_OBJECT'].contact_email if app.config.get('APP_CONFIG_OBJECT') else ''
        datasets_list = [
            {'id': d.id, 'name': d.config.company_name}
            for d in registry.values()
        ]
        from models.config import DEFAULT_PALETTE, DEFAULT_PRIMARY_COLOR
        common = {
            'current_lang': get_locale(),
            'supported_locales': supported_locales,
            'datasets': datasets_list,
        }
        if ds is None:
            return {
                **common,
                'company_name': 'My Company',
                'company_logo_url': '',
                'company_tagline': '',
                'company_email': contact_email,
                'current_dataset_id': '',
                'dataset_primary_color': DEFAULT_PRIMARY_COLOR,
                'dataset_palette': DEFAULT_PALETTE,
                'dataset_theme_style': '',
                'dataset_theme_overrides': {},
                'dataset_background_effect': 'particles',
                'dataset_card_effect': 'none',
                'hide_unavailable_modes': False,
            }
        return {
            **common,
            'company_name': ds.config.company_name,
            'company_logo_url': ds.config.logo_url,
            'company_tagline': ds.config.tagline,
            'company_email': contact_email,
            'current_dataset_id': ds.id,
            'dataset_primary_color': ds.config.primary_color,
            'dataset_palette': ds.config.palette,
            'dataset_theme_style': _theme_inline_style(ds.config.theme),
            'dataset_theme_overrides': ds.config.theme.overrides,
            'dataset_background_effect': ds.config.theme.background_effect,
            'dataset_card_effect': ds.config.theme.card_effect,
            'hide_unavailable_modes': ds.config.hide_unavailable_modes,
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
