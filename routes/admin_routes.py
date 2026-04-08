import os
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
from flask import Blueprint, jsonify, render_template, request, session
from flask_babel import gettext as _
from werkzeug.utils import secure_filename

from models.config import CompanyConfig

admin_bp = Blueprint('admin', __name__)

UPLOAD_DIR = Path('uploads')


def _is_authenticated() -> bool:
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if not admin_password:
        return True
    if session.get('admin_authenticated'):
        return True
    if request.args.get('password') == admin_password:
        session['admin_authenticated'] = True
        return True
    return False


@admin_bp.route('/setup')
def setup():
    if not _is_authenticated():
        return jsonify({'error': _('Unauthorized')}), 401

    current_config = {}
    try:
        config = CompanyConfig('config.yaml')
        current_config = {
            'company': {
                'name': config.company_name,
                'logo_url': config.logo_url,
                'contact_email': config.contact_email,
                'tagline': config.tagline,
            },
            'data': {
                'csv_path': config.csv_path,
                'images_dir': config.images_dir,
                'column_mapping': config.column_mapping,
            },
        }
    except (FileNotFoundError, ValueError):
        pass

    return render_template('setup.html', current_config=current_config)


@admin_bp.route('/setup/upload-csv', methods=['POST'])
def upload_csv():
    if not _is_authenticated():
        return jsonify({'error': _('Unauthorized')}), 401

    if 'file' not in request.files:
        return jsonify({'error': _('No file provided')}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': _('No file selected')}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.csv'):
        return jsonify({'error': _('File must be a CSV')}), 400

    UPLOAD_DIR.mkdir(exist_ok=True)
    filepath = UPLOAD_DIR / filename

    try:
        file.save(str(filepath))
        df = pd.read_csv(filepath, nrows=5)
    except Exception as e:
        filepath.unlink(missing_ok=True)
        return jsonify({'error': f'{_("Invalid CSV file")}: {e}'}), 400

    columns = list(df.columns)
    preview = df.head(5).fillna('').to_dict(orient='records')

    return jsonify({
        'columns': columns,
        'preview': preview,
        'filename': filename,
    })


@admin_bp.route('/setup/save', methods=['POST'])
def save_config():
    if not _is_authenticated():
        return jsonify({'error': _('Unauthorized')}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': _('No data provided')}), 400

    company = data.get('company', {})
    column_mapping = data.get('column_mapping', {})
    csv_filename = data.get('csv_filename', '')
    images_dir = data.get('images_dir', 'static/images')

    config_dict = {
        'company': {
            'name': company.get('name', ''),
            'logo_url': company.get('logo_url', ''),
            'contact_email': company.get('contact_email', ''),
            'tagline': company.get('tagline', ''),
        },
        'data': {
            'csv_path': csv_filename,
            'images_dir': images_dir,
            'column_mapping': column_mapping,
        },
    }

    try:
        CompanyConfig.save(config_dict)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'success': True})


@admin_bp.route('/setup/upload-photos', methods=['POST'])
def upload_photos():
    if not _is_authenticated():
        return jsonify({'error': _('Unauthorized')}), 401

    if 'file' not in request.files:
        return jsonify({'error': _('No file provided')}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': _('No file selected')}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.zip'):
        return jsonify({'error': _('File must be a ZIP archive')}), 400

    try:
        config = CompanyConfig('config.yaml')
        images_dir = Path(config.images_dir)
    except (FileNotFoundError, ValueError):
        images_dir = Path('static/images')

    images_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = tmp.name
        file.save(tmp_path)

    try:
        with zipfile.ZipFile(tmp_path, 'r') as zf:
            valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
            extracted = 0
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
