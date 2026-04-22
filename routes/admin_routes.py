import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for
from flask_babel import gettext as _
from werkzeug.utils import secure_filename

from models.config import OPTIONAL_FIELDS, REQUIRED_FIELDS, AppConfig, DatasetConfig
from models.dataset_registry import DatasetRegistry

_CANONICAL_FIELDS = list(REQUIRED_FIELDS) + list(OPTIONAL_FIELDS)
_VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

admin_bp = Blueprint('admin', __name__)

_DATASET_ID_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{0,31}$')


def _upload_dir() -> Path:
    return Path(current_app.config.get('UPLOAD_DIR', 'uploads'))


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

    return render_template(
        'setup_wizard.html',
        mode='new',
        dataset_id='',
        existing_ids=list(_registry().ids()),
        current_config={},
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
        },
        'data': {
            'csv_path': ds.config.csv_path,
            'images_dir': ds.config.images_dir,
            'column_mapping': ds.config.column_mapping,
        },
    }

    return render_template(
        'setup_wizard.html',
        mode='edit',
        dataset_id=dataset_id,
        existing_ids=[i for i in _registry().ids() if i != dataset_id],
        current_config=current_config,
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

    raw_tagline = company.get('tagline', '')
    # Wizard posts {fr, en}; legacy callers may still post a bare string.
    if isinstance(raw_tagline, dict):
        normalised_tagline: str | dict = {
            'fr': raw_tagline.get('fr', '').strip(),
            'en': raw_tagline.get('en', '').strip(),
        }
    else:
        normalised_tagline = str(raw_tagline).strip()

    new_ds_dict = {
        'company': {
            'name': company.get('name', ''),
            'logo_url': company.get('logo_url', ''),
            'tagline': normalised_tagline,
        },
        'data': {
            'csv_path': str(final_csv_path),
            'images_dir': str(photos_dir) if mode == 'new' else (existing.config.images_dir if existing else str(photos_dir)),
            'scores_db_path': existing.config.scores_db_path if existing else str(dataset_dir / 'scores.json'),
            'column_mapping': column_mapping,
        },
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

    return jsonify({'success': True, 'id': ds_id, 'redirect': url_for('admin.setup')})


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


@admin_bp.route('/setup/<dataset_id>/upload-photos', methods=['POST'])
def upload_photos(dataset_id):
    """Extract a photos ZIP into an existing dataset's images directory."""
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return jsonify({'error': _('Dataset not found')}), 404

    if 'file' not in request.files:
        return jsonify({'error': _('No file provided')}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': _('No file selected')}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.zip'):
        return jsonify({'error': _('File must be a ZIP archive')}), 400

    images_dir = Path(ds.config.images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = tmp.name
        file.save(tmp_path)

    extracted = 0
    try:
        with zipfile.ZipFile(tmp_path, 'r') as zf:
            valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
            for member in zf.infolist():
                if member.is_dir():
                    continue
                ext = Path(member.filename).suffix.lower()
                if ext not in valid_extensions:
                    continue
                safe_name = secure_filename(Path(member.filename).name)
                if not safe_name:
                    continue
                target = images_dir / safe_name
                with zf.open(member) as src, open(target, 'wb') as dst:
                    dst.write(src.read())
                extracted += 1
    except zipfile.BadZipFile:
        return jsonify({'error': _('Invalid ZIP file')}), 400
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return jsonify({'extracted': extracted})


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


@admin_bp.route('/setup/<dataset_id>/employees')
def employees_list(dataset_id):
    auth = _require_admin()
    if auth is not None:
        return auth

    ds = _registry().get(dataset_id)
    if ds is None:
        return redirect(url_for('admin.setup'))

    employees = ds.employee_data.get_all_employees()
    rows = []
    for idx, emp in enumerate(employees):
        rows.append({
            'idx': idx,
            'first_name': emp.get('first_name', ''),
            'last_name': emp.get('last_name', ''),
            'photo': emp.get('photo', ''),
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

    # Name the file after the employee to keep it predictable; fall back to
    # a safe filename if names are missing.
    first = str(employee.get('first_name', '')).strip()
    last = str(employee.get('last_name', '')).strip()
    base = secure_filename(f'{last}_{first}') or f'employee_{idx}'
    photo_filename = f'{base}{ext}'

    images_dir = Path(ds.config.images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)
    file.save(str(images_dir / photo_filename))

    ds.employee_data.update_at_index(idx, {'photo': photo_filename})
    try:
        ds.employee_data.save()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'success': True, 'photo': photo_filename})
