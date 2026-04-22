"""Integration tests for /setup admin API endpoints (multi-dataset CRUD)."""
import io
import os
import zipfile
from pathlib import Path

import pytest
import yaml

from app import create_app


@pytest.fixture(autouse=True)
def _no_admin_password():
    os.environ.pop('ADMIN_PASSWORD', None)
    yield
    os.environ.pop('ADMIN_PASSWORD', None)


@pytest.fixture
def legacy_app():
    """App built with the committed legacy test fixture (single 'default' dataset)."""
    return create_app('tests/fixtures/test_config.yaml')


@pytest.fixture
def legacy_client(legacy_app):
    return legacy_app.test_client()


@pytest.fixture
def isolated_app(tmp_path, monkeypatch):
    """Fresh app rooted in a tmp dir so save()/delete() don't touch the repo."""
    monkeypatch.chdir(tmp_path)
    csv = tmp_path / 'seed.csv'
    csv.write_text(
        'firstName,lastName,photo_path,team,jobTitle,company,sex\n'
        'Alice,Dupont,alice.jpg,Eng,Dev,Acme,F\n'
    )
    mapping = {
        'first_name': 'firstName', 'last_name': 'lastName', 'photo': 'photo_path',
        'team': 'team', 'job_title': 'jobTitle', 'company': 'company', 'sex': 'sex',
    }
    cfg_path = tmp_path / 'config.yaml'
    cfg_path.write_text(yaml.dump({
        'app': {'contact_email': 'admin@example.com', 'default_dataset': 'acme'},
        'datasets': {
            'acme': {
                'company': {'name': 'Acme Corp', 'logo_url': '/logo.png', 'tagline': 'Hi'},
                'data': {
                    'csv_path': str(csv),
                    'images_dir': str(tmp_path / 'data' / 'acme' / 'photos'),
                    'scores_db_path': str(tmp_path / 'data' / 'acme' / 'scores.json'),
                    'column_mapping': mapping,
                },
            },
        },
    }))
    app = create_app(str(cfg_path))
    app.config['UPLOAD_DIR'] = str(tmp_path / 'uploads')
    return app


@pytest.fixture
def isolated_client(isolated_app):
    return isolated_app.test_client()


class TestSetupListRoute:
    def test_landing_lists_datasets(self, isolated_client):
        resp = isolated_client.get('/setup')
        assert resp.status_code == 200
        assert b'Acme Corp' in resp.data
        assert b'data-dataset-id="acme"' in resp.data
        assert b'/setup/new' in resp.data  # "Add dataset" link

    def test_landing_empty_state_when_no_datasets(self, tmp_path):
        app = create_app(str(tmp_path / 'missing.yaml'))
        resp = app.test_client().get('/setup')
        # Empty registry → first-run redirect handler *lets* /setup through
        assert resp.status_code == 200
        # Empty state CTA visible
        assert b'setup/new' in resp.data or b'premier dataset' in resp.data.lower() or b'first dataset' in resp.data.lower()

    def test_requires_password_when_set(self, isolated_client):
        os.environ['ADMIN_PASSWORD'] = 'secret123'
        try:
            resp = isolated_client.get('/setup')
            assert resp.status_code == 401
        finally:
            os.environ.pop('ADMIN_PASSWORD', None)

    def test_accepts_password_in_query(self, isolated_client):
        os.environ['ADMIN_PASSWORD'] = 'secret123'
        try:
            resp = isolated_client.get('/setup?password=secret123')
            assert resp.status_code == 200
        finally:
            os.environ.pop('ADMIN_PASSWORD', None)


class TestSetupWizardRoutes:
    def test_new_wizard_loads(self, isolated_client):
        resp = isolated_client.get('/setup/new')
        assert resp.status_code == 200
        assert b'dataset-id' in resp.data
        assert b'company-name' in resp.data

    def test_edit_wizard_loads_for_existing(self, isolated_client):
        resp = isolated_client.get('/setup/acme/edit')
        assert resp.status_code == 200
        assert b'Acme Corp' in resp.data

    def test_edit_wizard_redirects_for_unknown(self, isolated_client):
        resp = isolated_client.get('/setup/ghost/edit', follow_redirects=False)
        assert resp.status_code == 302
        assert '/setup' in resp.headers['Location']


class TestUploadCsv:
    def test_returns_columns_and_preview(self, legacy_client):
        data = {'file': (io.BytesIO(b'firstName,lastName,team\nAlice,Dupont,Eng\n'), 'test.csv')}
        resp = legacy_client.post('/setup/upload-csv', data=data, content_type='multipart/form-data')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['columns'] == ['firstName', 'lastName', 'team']
        assert body['filename'] == 'test.csv'
        assert body['preview'][0]['firstName'] == 'Alice'

    def test_no_file_returns_400(self, legacy_client):
        resp = legacy_client.post('/setup/upload-csv', data={}, content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_non_csv_extension_returns_400(self, legacy_client):
        data = {'file': (io.BytesIO(b'hello'), 'document.txt')}
        resp = legacy_client.post('/setup/upload-csv', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400


class TestSaveDataset:
    def _valid_mapping(self):
        return {
            'first_name': 'firstName', 'last_name': 'lastName', 'photo': 'photo_path',
            'team': 'team', 'job_title': 'jobTitle', 'company': 'company', 'sex': 'sex',
        }

    def _upload_csv(self, client, filename='new.csv'):
        csv = b'firstName,lastName,photo_path,team,jobTitle,company,sex\nZoe,Roe,z.jpg,HR,Mgr,ClientX,F\n'
        resp = client.post('/setup/upload-csv',
                           data={'file': (io.BytesIO(csv), filename)},
                           content_type='multipart/form-data')
        assert resp.status_code == 200

    def test_new_mode_creates_dataset_and_hot_reloads(self, isolated_app, isolated_client):
        self._upload_csv(isolated_client, 'client_x.csv')

        payload = {
            'mode': 'new',
            'id': 'client_x',
            'company': {'name': 'Client X', 'logo_url': '', 'tagline': ''},
            'column_mapping': self._valid_mapping(),
            'csv_filename': 'client_x.csv',
        }
        resp = isolated_client.post('/setup/save', json=payload)
        assert resp.status_code == 200, resp.get_json()

        # Registry hot-reloaded
        registry = isolated_app.config['DATASET_REGISTRY']
        assert 'client_x' in registry.ids()
        assert registry.get('client_x').config.company_name == 'Client X'

    def test_new_mode_rejects_duplicate_id(self, isolated_client):
        self._upload_csv(isolated_client, 'dup.csv')
        payload = {
            'mode': 'new',
            'id': 'acme',
            'company': {'name': 'Other'},
            'column_mapping': self._valid_mapping(),
            'csv_filename': 'dup.csv',
        }
        resp = isolated_client.post('/setup/save', json=payload)
        assert resp.status_code == 409

    def test_new_mode_rejects_invalid_id(self, isolated_client):
        payload = {
            'mode': 'new',
            'id': 'Bad Id!',
            'company': {'name': 'Oops'},
            'column_mapping': self._valid_mapping(),
            'csv_filename': 'x.csv',
        }
        resp = isolated_client.post('/setup/save', json=payload)
        assert resp.status_code == 400

    def test_new_mode_requires_csv_upload(self, isolated_client):
        payload = {
            'mode': 'new',
            'id': 'no_csv',
            'company': {'name': 'NoCSV'},
            'column_mapping': self._valid_mapping(),
            'csv_filename': '',
        }
        resp = isolated_client.post('/setup/save', json=payload)
        assert resp.status_code == 400

    def test_edit_mode_updates_branding_without_csv_upload(self, isolated_app, isolated_client):
        payload = {
            'mode': 'edit',
            'id': 'acme',
            'company': {'name': 'Acme Renamed', 'logo_url': '/new.png', 'tagline': 'New'},
            'column_mapping': self._valid_mapping(),
            'csv_filename': '',
        }
        resp = isolated_client.post('/setup/save', json=payload)
        assert resp.status_code == 200, resp.get_json()
        assert isolated_app.config['DATASET_REGISTRY'].get('acme').config.company_name == 'Acme Renamed'

    def test_save_without_body_returns_400(self, isolated_client):
        resp = isolated_client.post('/setup/save', data='', content_type='application/json')
        assert resp.status_code == 400


class TestDeleteDataset:
    def test_removes_from_registry_and_disk(self, isolated_app, isolated_client, tmp_path):
        # Pre-create the data dir so delete can clean it up
        (tmp_path / 'data' / 'acme').mkdir(parents=True, exist_ok=True)
        (tmp_path / 'data' / 'acme' / 'team.csv').write_text('x')

        resp = isolated_client.post('/setup/acme/delete')
        assert resp.status_code == 200

        assert isolated_app.config['DATASET_REGISTRY'].get('acme') is None
        assert not (tmp_path / 'data' / 'acme').exists()

    def test_unknown_dataset_returns_404(self, isolated_client):
        resp = isolated_client.post('/setup/ghost/delete')
        assert resp.status_code == 404


class TestUploadPhotos:
    def test_extracts_valid_zip_into_dataset_images_dir(self, isolated_app, isolated_client, tmp_path):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('alice.jpg', b'fake jpg')
            zf.writestr('bob.png', b'fake png')
            zf.writestr('readme.txt', b'ignore')
        buf.seek(0)

        resp = isolated_client.post(
            '/setup/acme/upload-photos',
            data={'file': (buf, 'photos.zip')},
            content_type='multipart/form-data',
        )
        assert resp.status_code == 200
        assert resp.get_json()['extracted'] == 2

        images_dir = Path(isolated_app.config['DATASET_REGISTRY'].get('acme').config.images_dir)
        assert (images_dir / 'alice.jpg').exists()
        assert (images_dir / 'bob.png').exists()
        assert not (images_dir / 'readme.txt').exists()

    def test_unknown_dataset_returns_404(self, isolated_client):
        resp = isolated_client.post(
            '/setup/ghost/upload-photos',
            data={'file': (io.BytesIO(b'x'), 'f.zip')},
            content_type='multipart/form-data',
        )
        assert resp.status_code == 404

    def test_non_zip_returns_400(self, isolated_client):
        resp = isolated_client.post(
            '/setup/acme/upload-photos',
            data={'file': (io.BytesIO(b'not a zip'), 'file.jpg')},
            content_type='multipart/form-data',
        )
        assert resp.status_code == 400


class TestReplaceCsv:
    def _valid_mapping(self):
        return {
            'first_name': 'firstName', 'last_name': 'lastName', 'photo': 'photo_path',
            'team': 'team', 'job_title': 'jobTitle', 'company': 'company', 'sex': 'sex',
        }

    def test_replaces_csv_and_reloads_employee_data(self, isolated_app, isolated_client):
        new_csv = (
            b'firstName,lastName,photo_path,team,jobTitle,company,sex\n'
            b'Alice,Dupont,a.jpg,Eng,Dev,Acme,F\n'
            b'Bob,Martin,b.jpg,Sales,Rep,Acme,M\n'
            b'Carole,Zoe,c.jpg,HR,Lead,Acme,F\n'
        )
        isolated_client.post('/setup/upload-csv',
                             data={'file': (io.BytesIO(new_csv), 'new_acme.csv')},
                             content_type='multipart/form-data')

        resp = isolated_client.post('/setup/acme/replace-csv', json={'csv_filename': 'new_acme.csv'})
        assert resp.status_code == 200, resp.get_json()

        acme = isolated_app.config['DATASET_REGISTRY'].get('acme')
        assert acme is not None
        assert len(acme.employee_data.get_all_employees()) == 3
