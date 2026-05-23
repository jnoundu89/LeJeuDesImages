import io
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import yaml
from flask import Blueprint, current_app, jsonify, redirect, render_template, request, send_file, session, url_for
from flask_babel import gettext as _
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from models.config import (
    OPTIONAL_FIELDS,
    REQUIRED_FIELDS,
    AppConfig,
    DatasetConfig,
    DatasetTheme,
    normalise_color,
    normalise_palette,
)
from models.dataset_registry import DatasetRegistry

_CANONICAL_FIELDS = list(REQUIRED_FIELDS) + list(OPTIONAL_FIELDS)
_VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
_MAX_PHOTO_BYTES = 8 * 1024 * 1024  # 8 MiB — generous for hi-res phone photos.
_MAX_PHOTO_DIMENSION = 1200  # Resize to 1200px on the longest side before storing.
_JPEG_QUALITY = 85

admin_bp = Blueprint('admin', __name__)

_DATASET_ID_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{0,31}$')


def _validate_and_compress_image(raw_bytes: bytes) -> tuple[bytes, str] | None:
    """Validate + downscale an uploaded image.

    Returns ``(compressed_bytes, extension)`` when the bytes are a real
    image recognised by Pillow, or ``None`` when the payload is
    corrupted or oversize. The extension is returned without the dot
    and reflects the output format (always ``jpg`` for photos that
    don't need transparency, ``png`` for paletted / transparent).
    """
    if len(raw_bytes) > _MAX_PHOTO_BYTES:
        return None
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.verify()  # cheap structural check
    except (UnidentifiedImageError, OSError, ValueError):
        return None

    # `verify()` consumes the file; re-open for actual processing.
    img = Image.open(io.BytesIO(raw_bytes))
    img = img.convert('RGBA' if img.mode in ('RGBA', 'LA', 'P') else 'RGB')

    # Downscale to keep uploads snappy; preserve aspect ratio.
    # Image.LANCZOS was moved into Image.Resampling in Pillow 10; pyright
    # can't always follow the re-export, so resolve it dynamically.
    resample_filter = getattr(Image, 'LANCZOS', None) or Image.Resampling.LANCZOS
    img.thumbnail((_MAX_PHOTO_DIMENSION, _MAX_PHOTO_DIMENSION), resample_filter)

    out = io.BytesIO()
    if img.mode == 'RGBA':
        img.save(out, format='PNG', optimize=True)
        ext = 'png'
    else:
        img.save(out, format='JPEG', quality=_JPEG_QUALITY, optimize=True)
        ext = 'jpg'
    return out.getvalue(), ext


def _safe_under(base: Path, target: Path) -> bool:
    """True when ``target`` resolves inside ``base``.

    Belt-and-braces against path traversal on top of
    ``send_from_directory`` / ``secure_filename``.
    """
    try:
        base_r = base.resolve()
        target_r = target.resolve()
        return target_r == base_r or base_r in target_r.parents
    except (OSError, ValueError):
        return False


def _upload_dir() -> Path:
    return Path(current_app.config.get('UPLOAD_DIR', 'uploads'))


def _pending_photos_dir() -> Path:
    """Buffer directory for photos uploaded BEFORE the dataset exists.

    Used during the « new dataset » wizard flow: photos uploaded in
    step 4 land here, then get moved into ``data/<id>/photos/`` when
    the user finalises the dataset in step 5. Cleared on GET /setup/new
    so a fresh wizard session never inherits leftovers from an
    abandoned previous session.
    """
    return _upload_dir() / 'pending_photos'


def _extract_photos_zip(zip_path: Path, target_dir: Path) -> int:
    """Extract image entries from a ZIP into ``target_dir``, flat.

    Returns the number of images extracted. Strips any directory
    components the archive may carry (so ``output/photos/X.jpg``
    lands as ``X.jpg``), and ignores non-image members + zip slip
    attempts via ``secure_filename``.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    extracted = 0
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            ext = Path(member.filename).suffix.lower()
            if ext not in valid_extensions:
                continue
            safe_name = secure_filename(Path(member.filename).name)
            if not safe_name:
                continue
            target = target_dir / safe_name
            with zf.open(member) as src, open(target, 'wb') as dst:
                dst.write(src.read())
            extracted += 1
    return extracted


def _registry() -> DatasetRegistry:
    return current_app.config['DATASET_REGISTRY']


def _app_config() -> AppConfig | None:
    return current_app.config.get('APP_CONFIG_OBJECT')


def _config_path() -> str:
    return current_app.config.get('CONFIG_PATH', 'config.yaml')


def _is_authenticated() -> bool:
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if not admin_password:
        return True
    if session.get('admin_authenticated'):
        return True
    # Back-compat: allow ?password=... for bookmarks / automation. The login
    # form is the preferred interactive path.
    if request.args.get('password') == admin_password:
        session['admin_authenticated'] = True
        return True
    return False


def _first_run_bypass() -> bool:
    """Allow unauthenticated /setup access when no dataset is configured yet.

    Without this, a fresh install that set ADMIN_PASSWORD would be locked out
    of the wizard with no way in (the login form itself is under /setup).
    """
    return _registry().is_empty()


def _require_admin():
    """Deny-or-redirect helper used by every protected view.

    Returns a response if the caller should NOT proceed, or None if auth is OK.
    HTML GETs are redirected to the login page; state-changing requests and
    JSON clients get a 401 JSON body.
    """
    if _is_authenticated() or _first_run_bypass():
        return None
    wants_json = (
        request.method != 'GET'
        or request.is_json
        or 'application/json' in (request.accept_mimetypes.best or '')
    )
    if wants_json:
        return jsonify({'error': _('Unauthorized')}), 401
    return redirect(url_for('admin.setup_login', next=request.full_path.rstrip('?')))


def _unauthorized():
    # Retained for callers that prefer the terse deny.
    return jsonify({'error': _('Unauthorized')}), 401


def _safe_next(raw: str | None) -> str:
    """Only allow redirects back to internal /setup* paths."""
    if not raw:
        return url_for('admin.setup')
    if raw.startswith('/setup'):
        return raw
    return url_for('admin.setup')


@admin_bp.route('/setup/login', methods=['GET', 'POST'])
def setup_login():
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if not admin_password or _is_authenticated():
        return redirect(_safe_next(request.args.get('next') or request.form.get('next')))

    error = None
    if request.method == 'POST':
        submitted = request.form.get('password', '')
        if submitted == admin_password:
            session['admin_authenticated'] = True
            return redirect(_safe_next(request.form.get('next')))
        error = _('Mot de passe incorrect.')

    return render_template(
        'setup_login.html',
        error=error,
        next_url=request.args.get('next') or request.form.get('next') or url_for('admin.setup'),
    )


@admin_bp.route('/setup/logout', methods=['POST'])
def setup_logout():
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin.setup_login'))


def _write_config_yaml(datasets_dict: dict, contact_email: str, default_id: str):
    payload = {
        'app': {
            'contact_email': contact_email,
            'default_dataset': default_id,
        },
        'datasets': datasets_dict,
    }
    AppConfig.save(payload, _config_path())


def _serialize_registry(exclude: str | None = None) -> dict:
    """Serialize registry datasets to a dict suitable for config.yaml."""
    out = {}
    for ds in _registry().values():
        if ds.id == exclude:
            continue
        out[ds.id] = ds.config.to_dict()
    return out


def _current_contact_email() -> str:
    cfg = _app_config()
    return cfg.contact_email if cfg is not None else ''


@admin_bp.route('/setup')
def setup():
    """Landing: list datasets, provide actions."""
    auth = _require_admin()
    if auth is not None:
        return auth

    registry = _registry()
    datasets_info = []
    for ds in registry.values():
        try:
            employee_count = len(ds.employee_data.get_all_employees())
        except Exception:
            employee_count = 0
        datasets_info.append({
            'id': ds.id,
            'name': ds.config.company_name,
            'logo_url': ds.config.logo_url,
            'employee_count': employee_count,
            'csv_path': ds.config.csv_path,
            'images_dir': ds.config.images_dir,
        })

    return render_template(
        'setup_list.html',
        datasets=datasets_info,
        contact_email=_current_contact_email(),
        default_dataset_id=registry.default_id,
    )


@admin_bp.route('/setup/new')
def setup_new():
    """Wizard: add a new dataset."""
    auth = _require_admin()
    if auth is not None:
        return auth

    # Reset the pre-creation photo buffer so a fresh wizard session
    # never inherits photos from an abandoned prior session.
    pending = _pending_photos_dir()
    if pending.exists():
        for child in pending.iterdir():
            if child.is_file():
                child.unlink()

    return render_template(
        'setup_wizard.html',
        mode='new',
        dataset_id='',
        existing_ids=list(_registry().ids()),
        current_config={},
        current_palette='corporate',
        current_overrides={},
        # New wizard step: animated background. None means « inherit
        # the palette's default » (particles for everyone, fireworks
        # for legacy). The wizard renders an "Auto" / "Particles" /
        # "Fireworks" radio off this value.
        current_background_effect=None,
        current_card_effect=None,
        # Brand-new datasets don't have any preset slots yet — the
        # presets section is hidden in NEW mode anyway.
        current_presets={},
    )


@admin_bp.route('/setup/<dataset_id>/edit')
def setup_edit(dataset_id):
    """Wizard: edit an existing dataset's config (branding + mapping)."""
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return redirect(url_for('admin.setup'))

    current_config = {
        'company': {
            'name': ds.config.company_name,
            'logo_url': ds.config.logo_url,
            'tagline': ds.config.tagline,
            'taglines': ds.config.taglines,
            # primary_color + palette kept on company for back-compat
            # with the current wizard (Phase 3 will move this to
            # `theme`). Sourced from ds.config.theme so the value is
            # always the resolved one.
            'primary_color': ds.config.primary_color,
            'palette': ds.config.palette,
        },
        'theme': {
            'palette': ds.config.theme.palette,
            'overrides': ds.config.theme.overrides,
        },
        'data': {
            'csv_path': ds.config.csv_path,
            'images_dir': ds.config.images_dir,
            'column_mapping': ds.config.column_mapping,
        },
        'settings': {
            'hide_unavailable_modes': ds.config.hide_unavailable_modes,
        },
    }

    return render_template(
        'setup_wizard.html',
        mode='edit',
        dataset_id=dataset_id,
        existing_ids=[i for i in _registry().ids() if i != dataset_id],
        current_config=current_config,
        current_palette=ds.config.theme.palette,
        current_overrides=ds.config.theme.overrides,
        # The raw stored value (None when defaulted by palette).
        # The wizard's third radio « Auto » is the chosen state when
        # this is None.
        current_background_effect=ds.config.theme.background_effect_explicit,
        current_card_effect=ds.config.theme.card_effect_explicit,
        # Saved theme presets — rendered as a list of cards with
        # Apply / Delete buttons in the wizard's Thème step.
        current_presets=ds.config.theme.presets,
    )


@admin_bp.route('/setup/upload-csv', methods=['POST'])
def upload_csv():
    """Validate uploaded CSV, return columns + preview. CSV stays in uploads/ until save."""
    auth = _require_admin()
    if auth is not None:
        return auth

    if 'file' not in request.files:
        return jsonify({'error': _('No file provided')}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': _('No file selected')}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.csv'):
        return jsonify({'error': _('File must be a CSV')}), 400

    upload_dir = _upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / filename

    try:
        file.save(str(filepath))
        df = pd.read_csv(filepath, nrows=5)
    except Exception as e:
        filepath.unlink(missing_ok=True)
        return jsonify({'error': f'{_("Invalid CSV file")}: {e}'}), 400

    return jsonify({
        'columns': list(df.columns),
        'preview': df.head(5).fillna('').to_dict(orient='records'),
        'filename': filename,
    })


@admin_bp.route('/setup/save', methods=['POST'])
def save():
    """Create or update a dataset. Writes config.yaml + moves CSV to data/<id>/ + hot-reloads registry."""
    auth = _require_admin()
    if auth is not None:
        return auth

    data = request.get_json()
    if not data:
        return jsonify({'error': _('No data provided')}), 400

    mode = data.get('mode', 'new')
    ds_id = (data.get('id') or '').strip()
    if not _DATASET_ID_RE.match(ds_id):
        return jsonify({'error': _('Dataset id must be lowercase alphanumeric (underscores and dashes allowed, max 32 chars).')}), 400

    registry = _registry()
    existing = registry.get(ds_id)
    if mode == 'new' and existing is not None:
        return jsonify({'error': _('A dataset with this id already exists.')}), 409

    company = data.get('company', {})
    column_mapping = data.get('column_mapping', {})
    csv_filename = (data.get('csv_filename') or '').strip()

    dataset_dir = Path('data') / ds_id
    dataset_dir.mkdir(parents=True, exist_ok=True)
    photos_dir = dataset_dir / 'photos'
    photos_dir.mkdir(parents=True, exist_ok=True)

    final_csv_path = dataset_dir / 'team.csv'

    # If a fresh CSV was uploaded, move it from uploads/ to the dataset dir
    if csv_filename:
        uploaded = _upload_dir() / secure_filename(csv_filename)
        if uploaded.exists():
            shutil.move(str(uploaded), str(final_csv_path))
        elif not final_csv_path.exists():
            return jsonify({'error': _('Uploaded CSV was not found. Re-upload and retry.')}), 400
    elif existing is not None:
        # Edit mode: reuse existing CSV path
        final_csv_path = Path(existing.config.csv_path)
    else:
        return jsonify({'error': _('A CSV file is required to create a dataset.')}), 400

    # New mode: drain the pending-photos buffer (uploaded in step 4)
    # into this dataset's photos dir. Each file is moved (not copied)
    # so the buffer ends up empty for the next wizard session.
    if mode == 'new':
        pending = _pending_photos_dir()
        if pending.exists():
            for src in list(pending.iterdir()):
                if src.is_file():
                    target = photos_dir / src.name
                    if _safe_under(photos_dir, target):
                        shutil.move(str(src), str(target))

    raw_tagline = company.get('tagline', '')
    # Wizard posts {fr, en}; legacy callers may still post a bare string.
    if isinstance(raw_tagline, dict):
        normalised_tagline: str | dict = {
            'fr': raw_tagline.get('fr', '').strip(),
            'en': raw_tagline.get('en', '').strip(),
        }
    else:
        normalised_tagline = str(raw_tagline).strip()

    # Theme: prefer the new nested `theme: {palette, overrides}` payload
    # (what Phase 3 wizard will send). Fall back to the legacy flat
    # fields `company.palette` + `company.primary_color` for any
    # caller or YAML that hasn't migrated yet. DatasetTheme handles
    # validation of both paths identically (unknown tokens dropped,
    # invalid hex dropped, unknown palette → corporate).
    theme_raw = data.get('theme')
    if isinstance(theme_raw, dict):
        theme = DatasetTheme(theme_raw)
    else:
        legacy_primary = normalise_color(company.get('primary_color'))
        theme = DatasetTheme({
            'palette': normalise_palette(company.get('palette')),
            # Only store a primary override when it differs from the
            # default — matches the DatasetTheme.from_raw_company
            # rule so re-saving a default-primary dataset doesn't
            # silently promote it to an override.
            'overrides': (
                {'primary': legacy_primary}
                if legacy_primary.upper() != '#4F46E5' else {}
            ),
        })

    company_block: dict = {
        'name': company.get('name', ''),
        'logo_url': company.get('logo_url', ''),
        'tagline': normalised_tagline,
    }

    settings_raw = data.get('settings') or {}
    settings_block = {
        'hide_unavailable_modes': bool(settings_raw.get('hide_unavailable_modes', False)),
    }

    new_ds_dict: dict = {
        'company': company_block,
        'theme': theme.to_dict(),
        'data': {
            'csv_path': str(final_csv_path),
            'images_dir': str(photos_dir) if mode == 'new' else (existing.config.images_dir if existing else str(photos_dir)),
            'scores_db_path': existing.config.scores_db_path if existing else str(dataset_dir / 'scores.json'),
            'column_mapping': column_mapping,
        },
        'settings': settings_block,
    }

    # Validate by instantiating a DatasetConfig before writing
    try:
        new_ds_config = DatasetConfig(ds_id, new_ds_dict)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    datasets_dict = _serialize_registry(exclude=ds_id)
    datasets_dict[ds_id] = new_ds_config.to_dict()

    contact_email = data.get('contact_email') or _current_contact_email()
    default_id = registry.default_id or ds_id

    try:
        _write_config_yaml(datasets_dict, contact_email, default_id)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Hot-reload: remove the old Dataset (if any) and rebuild
    if existing is not None:
        registry.remove(ds_id)
    registry.add(new_ds_config)

    # Refresh AppConfig object on app for contact_email changes
    try:
        current_app.config['APP_CONFIG_OBJECT'] = AppConfig(_config_path())
    except Exception:
        pass

    # Compute photos referenced by the CSV but missing on disk so the
    # wizard can show a non-blocking warning toast pointing the admin
    # to what to upload next. Empty list means all photos resolved.
    fresh_ds = registry.get(ds_id)
    missing_photos = _missing_photos_for(fresh_ds) if fresh_ds is not None else []

    return jsonify({
        'success': True,
        'id': ds_id,
        'redirect': url_for('admin.setup'),
        'warnings': {'missing_photos': missing_photos},
    })


def _persist_dataset_with_new_theme(ds_id: str, ds, new_theme: DatasetTheme):
    """Rebuild the dataset with a swapped theme + flush to disk + hot-reload.

    Shared by the preset apply / delete routes. Other dataset config
    (CSV path, photos, settings, column mapping) is preserved verbatim.
    """
    raw = ds.config.to_dict()
    raw['theme'] = new_theme.to_dict()
    new_ds_config = DatasetConfig(ds_id, raw)

    registry = _registry()
    datasets_dict = _serialize_registry(exclude=ds_id)
    datasets_dict[ds_id] = new_ds_config.to_dict()

    contact_email = _current_contact_email()
    default_id = registry.default_id or ds_id
    _write_config_yaml(datasets_dict, contact_email, default_id)

    registry.remove(ds_id)
    registry.add(new_ds_config)


@admin_bp.route('/setup/<dataset_id>/theme/preset/<preset_name>/apply', methods=['POST'])
def apply_theme_preset(dataset_id, preset_name):
    """Swap the dataset's active theme to the named preset."""
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return jsonify({'error': _('Dataset not found')}), 404

    presets = ds.config.theme.presets
    if preset_name not in presets:
        return jsonify({'error': _('Preset not found')}), 404

    preset = presets[preset_name]
    # Rebuild the theme from the preset, keeping the existing presets
    # dict intact so the user can switch back and forth.
    new_theme_raw = {
        'palette': preset['palette'],
        'overrides': preset.get('overrides', {}),
        'presets': ds.config.theme.presets,  # preserve the saved set
    }
    if 'background_effect' in preset:
        new_theme_raw['background_effect'] = preset['background_effect']

    try:
        _persist_dataset_with_new_theme(dataset_id, ds, DatasetTheme(new_theme_raw))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'success': True, 'preset': preset_name})


@admin_bp.route('/setup/<dataset_id>/theme/preset/<preset_name>/delete', methods=['POST'])
def delete_theme_preset(dataset_id, preset_name):
    """Remove a saved preset from the dataset's theme.presets dict."""
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return jsonify({'error': _('Dataset not found')}), 404

    presets = ds.config.theme.presets
    if preset_name not in presets:
        return jsonify({'error': _('Preset not found')}), 404

    # Build a new theme keeping everything intact except for the dropped preset.
    remaining = {k: v for k, v in presets.items() if k != preset_name}
    new_theme_raw = {
        'palette': ds.config.theme.palette,
        'overrides': ds.config.theme.overrides,
        'presets': remaining,
    }
    if ds.config.theme.background_effect_explicit is not None:
        new_theme_raw['background_effect'] = ds.config.theme.background_effect_explicit

    try:
        _persist_dataset_with_new_theme(dataset_id, ds, DatasetTheme(new_theme_raw))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'success': True})


@admin_bp.route('/setup/<dataset_id>/delete', methods=['POST'])
def delete(dataset_id):
    """Remove a dataset entirely: disk + registry + config.yaml."""
    auth = _require_admin()
    if auth is not None:
        return auth

    registry = _registry()
    ds = registry.get(dataset_id)
    if ds is None:
        return jsonify({'error': _('Dataset not found')}), 404

    dataset_dir = Path('data') / dataset_id
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir, ignore_errors=True)

    registry.remove(dataset_id)

    datasets_dict = _serialize_registry()
    try:
        _write_config_yaml(
            datasets_dict,
            _current_contact_email(),
            registry.default_id,
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'success': True, 'redirect': url_for('admin.setup')})


def _accept_photos_zip(target_dir: Path):
    """Common implementation for the two photo-upload routes.

    Returns either a Flask response (on error) or a JSON-serialisable
    dict the caller can wrap into jsonify(). Both routes drop the
    archive into a temp file, run :func:`_extract_photos_zip`, and
    clean up regardless of outcome.
    """
    if 'file' not in request.files:
        return jsonify({'error': _('No file provided')}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': _('No file selected')}), 400
    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.zip'):
        return jsonify({'error': _('File must be a ZIP archive')}), 400

    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = Path(tmp.name)
        file.save(str(tmp_path))
    try:
        extracted = _extract_photos_zip(tmp_path, target_dir)
    except zipfile.BadZipFile:
        return jsonify({'error': _('Invalid ZIP file')}), 400
    finally:
        tmp_path.unlink(missing_ok=True)
    return jsonify({'extracted': extracted})


@admin_bp.route('/setup/<dataset_id>/upload-photos', methods=['POST'])
def upload_photos(dataset_id):
    """Extract a photos ZIP into an existing dataset's images directory."""
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return jsonify({'error': _('Dataset not found')}), 404

    return _accept_photos_zip(Path(ds.config.images_dir))


@admin_bp.route('/setup/upload-photos-pending', methods=['POST'])
def upload_photos_pending():
    """Buffer a photos ZIP for a dataset being created (no id yet).

    Files extract into ``uploads/pending_photos/``; the save handler
    moves them into ``data/<id>/photos/`` when the wizard finishes
    in step 5. Mirrors the ``/setup/upload-csv`` flow (which buffers
    the CSV the same way before dataset creation).
    """
    auth = _require_admin()
    if auth is not None:
        return auth
    return _accept_photos_zip(_pending_photos_dir())


@admin_bp.route('/setup/<dataset_id>/replace-csv', methods=['POST'])
def replace_csv(dataset_id):
    """Replace an existing dataset's CSV with a new upload (kept in uploads/ → moved here).

    Expects JSON {'csv_filename': str} referencing a CSV previously validated via /setup/upload-csv.
    """
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return jsonify({'error': _('Dataset not found')}), 404

    data = request.get_json() or {}
    csv_filename = (data.get('csv_filename') or '').strip()
    if not csv_filename:
        return jsonify({'error': _('csv_filename is required')}), 400

    uploaded = _upload_dir() / secure_filename(csv_filename)
    if not uploaded.exists():
        return jsonify({'error': _('Uploaded CSV was not found. Re-upload and retry.')}), 400

    target = Path(ds.config.csv_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(uploaded), str(target))

    # Hot-reload the dataset so EmployeeData re-reads the new CSV
    new_config = DatasetConfig(ds.id, ds.config.to_dict())
    _registry().remove(ds.id)
    _registry().add(new_config)

    return jsonify({'success': True})


# -- Employee CRUD --

def _employee_payload_from_request(data: dict) -> dict:
    """Extract a canonical-named employee dict from a JSON payload, skipping unknowns."""
    return {k: (data.get(k) or '') for k in _CANONICAL_FIELDS if k in data}


def _missing_photos_for(ds) -> list[str]:
    """Return the list of photo filenames referenced by the CSV but
    absent from the dataset's images_dir.

    Used to surface a warning at save time + to badge employee rows
    in the list view. The dataset's photo column is canonicalised
    on load so every value is `/photos/<filename>` — we just strip
    the prefix and check the file system.
    """
    images_dir = Path(ds.config.images_dir)
    missing: list[str] = []
    for emp in ds.employee_data.get_all_employees():
        photo = (emp.get('photo') or '').strip()
        if not photo:
            continue
        filename = photo.removeprefix('/photos/')
        if not (images_dir / filename).exists():
            missing.append(filename)
    return missing


@admin_bp.route('/setup/<dataset_id>/employees')
def employees_list(dataset_id):
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return redirect(url_for('admin.setup'))

    images_dir = Path(ds.config.images_dir)
    employees = ds.employee_data.get_all_employees()
    rows = []
    for idx, emp in enumerate(employees):
        photo = (emp.get('photo') or '').strip()
        # Flag missing photos per-row so the template can render an
        # alert badge next to the placeholder thumbnail.
        photo_missing = False
        if photo:
            filename = photo.removeprefix('/photos/')
            photo_missing = not (images_dir / filename).exists()
        rows.append({
            'idx': idx,
            'first_name': emp.get('first_name', ''),
            'last_name': emp.get('last_name', ''),
            'photo': photo,
            'photo_missing': photo_missing,
            'team': emp.get('team', ''),
            'job_title': emp.get('job_title', ''),
        })

    return render_template(
        'employees_list.html',
        dataset_id=dataset_id,
        dataset_name=ds.config.company_name,
        employees=rows,
    )


@admin_bp.route('/setup/<dataset_id>/employees/new')
def employee_new(dataset_id):
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return redirect(url_for('admin.setup'))

    blank = {field: '' for field in _CANONICAL_FIELDS}
    return render_template(
        'employee_edit.html',
        mode='new',
        dataset_id=dataset_id,
        dataset_name=ds.config.company_name,
        employee=blank,
        idx=None,
        required_fields=sorted(REQUIRED_FIELDS),
        optional_fields=sorted(OPTIONAL_FIELDS),
    )


@admin_bp.route('/setup/<dataset_id>/employees/<int:idx>/edit')
def employee_edit(dataset_id, idx):
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return redirect(url_for('admin.setup'))

    try:
        employee = ds.employee_data.get_by_index(idx)
    except IndexError:
        return redirect(url_for('admin.employees_list', dataset_id=dataset_id))

    emp_dict = {field: employee.get(field, '') for field in _CANONICAL_FIELDS}

    return render_template(
        'employee_edit.html',
        mode='edit',
        dataset_id=dataset_id,
        dataset_name=ds.config.company_name,
        employee=emp_dict,
        idx=idx,
        required_fields=sorted(REQUIRED_FIELDS),
        optional_fields=sorted(OPTIONAL_FIELDS),
    )


@admin_bp.route('/setup/<dataset_id>/employees', methods=['POST'])
def employee_create(dataset_id):
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return jsonify({'error': _('Dataset not found')}), 404

    data = request.get_json() or {}
    fields = _employee_payload_from_request(data)

    missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]
    if missing:
        return jsonify({'error': _('Missing required fields: %(fields)s', fields=', '.join(sorted(missing)))}), 400

    idx = ds.employee_data.append(fields)
    try:
        ds.employee_data.save()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'success': True, 'idx': idx})


@admin_bp.route('/setup/<dataset_id>/employees/<int:idx>', methods=['POST'])
def employee_update(dataset_id, idx):
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return jsonify({'error': _('Dataset not found')}), 404

    data = request.get_json() or {}
    fields = _employee_payload_from_request(data)

    missing = [f for f in REQUIRED_FIELDS if f in fields and not fields.get(f)]
    if missing:
        return jsonify({'error': _('Missing required fields: %(fields)s', fields=', '.join(sorted(missing)))}), 400

    try:
        ds.employee_data.update_at_index(idx, fields)
    except IndexError:
        return jsonify({'error': _('Employee not found')}), 404

    try:
        ds.employee_data.save()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'success': True})


@admin_bp.route('/setup/<dataset_id>/employees/<int:idx>/delete', methods=['POST'])
def employee_delete(dataset_id, idx):
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return jsonify({'error': _('Dataset not found')}), 404

    try:
        ds.employee_data.delete_at_index(idx)
    except IndexError:
        return jsonify({'error': _('Employee not found')}), 404

    try:
        ds.employee_data.save()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'success': True})


@admin_bp.route('/setup/<dataset_id>/export')
def export_dataset(dataset_id):
    """Stream a ZIP archive of the dataset: CSV + photos + manifest.

    The archive layout is the one ``import_dataset`` expects:
        manifest.json   # dataset config (company + settings + mapping)
        team.csv        # employee CSV
        photos/*        # every file in images_dir
    """
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return jsonify({'error': _('Dataset not found')}), 404

    csv_path = Path(ds.config.csv_path)
    images_dir = Path(ds.config.images_dir)

    manifest = {
        'dataset_id': ds.id,
        'config': ds.config.to_dict(),
        # images_dir / csv_path are rewritten on import to the new dataset
        # layout — keep them out of the portable manifest.
        'schema_version': 1,
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('manifest.json', json.dumps(manifest, indent=2, ensure_ascii=False))
        if csv_path.exists():
            zf.write(csv_path, arcname='team.csv')
        if images_dir.exists():
            for photo in sorted(images_dir.iterdir()):
                if photo.is_file() and photo.suffix.lower() in _VALID_IMAGE_EXTENSIONS:
                    zf.write(photo, arcname=f'photos/{photo.name}')

    buf.seek(0)
    return send_file(
        buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{ds.id}.zip',
    )


@admin_bp.route('/setup/import', methods=['POST'])
def import_dataset():
    """Accept a ZIP built by /setup/<id>/export and create a new dataset.

    The target dataset id comes from a ``dataset_id`` form field (admin
    can rename on import so two users don't clash). We refuse to
    overwrite an existing id to keep this idempotent.
    """
    auth = _require_admin()
    if auth is not None:
        return auth

    if 'file' not in request.files:
        return jsonify({'error': _('No file provided')}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': _('No file selected')}), 400

    target_id = (request.form.get('dataset_id') or '').strip()
    if not _DATASET_ID_RE.match(target_id):
        return jsonify({'error': _('Invalid dataset id')}), 400
    if _registry().get(target_id) is not None:
        return jsonify({'error': _('A dataset with this id already exists.')}), 409

    # Stage the ZIP to a temp file so we can read it twice safely.
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = tmp.name
        file.save(tmp_path)

    try:
        with zipfile.ZipFile(tmp_path, 'r') as zf:
            names = set(zf.namelist())
            if 'manifest.json' not in names or 'team.csv' not in names:
                return jsonify({'error': _('Archive must contain manifest.json and team.csv')}), 400

            manifest = json.loads(zf.read('manifest.json').decode('utf-8'))

            # Stage new dataset on disk.
            dataset_dir = Path('data') / target_id
            if dataset_dir.exists():
                return jsonify({'error': _('Target dataset dir already exists')}), 409
            dataset_dir.mkdir(parents=True, exist_ok=True)
            photos_dir = dataset_dir / 'photos'
            photos_dir.mkdir(parents=True, exist_ok=True)

            # Write CSV
            (dataset_dir / 'team.csv').write_bytes(zf.read('team.csv'))

            # Extract every photo under photos/ using secure_filename.
            photo_count = 0
            for name in names:
                if not name.startswith('photos/') or name == 'photos/':
                    continue
                tail = secure_filename(Path(name).name)
                if not tail or Path(tail).suffix.lower() not in _VALID_IMAGE_EXTENSIONS:
                    continue
                target = photos_dir / tail
                if not _safe_under(photos_dir, target):
                    continue
                target.write_bytes(zf.read(name))
                photo_count += 1

        # Rebuild the DatasetConfig block from the manifest, rewriting
        # paths to the new dataset dir.
        config_block = manifest.get('config', {})
        data_block = dict(config_block.get('data', {}))
        data_block['csv_path'] = str(dataset_dir / 'team.csv')
        data_block['images_dir'] = str(photos_dir)
        data_block['scores_db_path'] = str(dataset_dir / 'scores.json')

        new_ds_dict: dict = {
            'company': dict(config_block.get('company', {})),
            'data': data_block,
        }
        # Preserve the theme block (palette + overrides) so custom
        # colors survive export → import, same as settings.
        # DatasetConfig will also fall back to legacy flat
        # company.palette / company.primary_color if `theme` is
        # absent (back-compat with pre-Phase-1 archives).
        if 'theme' in config_block:
            new_ds_dict['theme'] = dict(config_block['theme'])
        if 'settings' in config_block:
            new_ds_dict['settings'] = dict(config_block['settings'])

        try:
            new_ds_config = DatasetConfig(target_id, new_ds_dict)
        except ValueError as e:
            shutil.rmtree(dataset_dir, ignore_errors=True)
            return jsonify({'error': str(e)}), 400
    except zipfile.BadZipFile:
        return jsonify({'error': _('Invalid ZIP file')}), 400
    except (KeyError, json.JSONDecodeError, yaml.YAMLError) as e:
        return jsonify({'error': f'{_("Invalid archive")}: {e}'}), 400
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    # Persist + hot-reload
    datasets_dict = _serialize_registry()
    datasets_dict[target_id] = new_ds_config.to_dict()
    try:
        _write_config_yaml(datasets_dict, _current_contact_email(), _registry().default_id or target_id)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    _registry().add(new_ds_config)

    return jsonify({
        'success': True,
        'id': target_id,
        'photos_extracted': photo_count,
        'redirect': url_for('admin.setup'),
    })


@admin_bp.route('/setup/<dataset_id>/cleanup-photos', methods=['POST'])
def cleanup_orphan_photos(dataset_id):
    """Remove photos on disk that no employee CSV row references.

    GET /setup/<id>/cleanup-photos?preview=1 returns the list without
    deleting, POST with `confirm=1` actually removes them. Admin-only.
    """
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return jsonify({'error': _('Dataset not found')}), 404

    images_dir = Path(ds.config.images_dir)
    if not images_dir.exists():
        return jsonify({'orphans': [], 'removed': 0})

    # Collect the `photo` value referenced by every employee row.
    referenced: set[str] = set()
    for emp in ds.employee_data.get_all_employees():
        photo = str(emp.get('photo', '') or '').strip()
        if not photo:
            continue
        # CSV values can be full paths or just filenames; keep the tail.
        referenced.add(Path(photo).name)

    orphans: list[str] = []
    for entry in images_dir.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in _VALID_IMAGE_EXTENSIONS:
            continue
        if entry.name not in referenced:
            orphans.append(entry.name)

    data = request.get_json(silent=True) or {}
    if data.get('confirm'):
        removed = 0
        for name in orphans:
            target = images_dir / name
            if _safe_under(images_dir, target):
                try:
                    target.unlink()
                    removed += 1
                except OSError:
                    pass
        return jsonify({'orphans': orphans, 'removed': removed})

    # Preview only
    return jsonify({'orphans': orphans, 'removed': 0})


@admin_bp.route('/setup/<dataset_id>/employees/<int:idx>/photo', methods=['POST'])
def employee_upload_photo(dataset_id, idx):
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return jsonify({'error': _('Dataset not found')}), 404

    try:
        employee = ds.employee_data.get_by_index(idx)
    except IndexError:
        return jsonify({'error': _('Employee not found')}), 404

    if 'file' not in request.files:
        return jsonify({'error': _('No file provided')}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': _('No file selected')}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in _VALID_IMAGE_EXTENSIONS:
        return jsonify({'error': _('Unsupported image format')}), 400

    raw_bytes = file.read()
    processed = _validate_and_compress_image(raw_bytes)
    if processed is None:
        return jsonify({'error': _('Invalid or oversize image (max 8 MiB)')}), 400
    data, out_ext = processed

    # Name the file after the employee to keep it predictable; fall back to
    # a safe filename if names are missing.
    first = str(employee.get('first_name', '')).strip()
    last = str(employee.get('last_name', '')).strip()
    base = secure_filename(f'{last}_{first}') or f'employee_{idx}'
    photo_filename = f'{base}.{out_ext}'

    images_dir = Path(ds.config.images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)
    target = images_dir / photo_filename
    if not _safe_under(images_dir, target):
        return jsonify({'error': _('Invalid path')}), 400
    target.write_bytes(data)

    ds.employee_data.update_at_index(idx, {'photo': photo_filename})
    try:
        ds.employee_data.save()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Read back the canonicalised value (`/photos/<filename>`) so the
    # client gets a directly-usable URL for the <img src> swap.
    canonical_photo = ds.employee_data.get_by_index(idx).get('photo', '')
    return jsonify({'success': True, 'photo': canonical_photo})
