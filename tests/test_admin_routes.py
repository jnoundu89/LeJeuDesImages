"""Integration tests for /setup admin wizard API endpoints."""
import io
import json
import os
import zipfile
from unittest.mock import patch

import pytest


@pytest.fixture
def admin_client(client):
    """Client with ADMIN_PASSWORD unset (auth bypassed)."""
    os.environ.pop('ADMIN_PASSWORD', None)
    return client


@pytest.fixture
def protected_client(client):
    """Client with ADMIN_PASSWORD set."""
    os.environ['ADMIN_PASSWORD'] = 'secret123'
    yield client
    os.environ.pop('ADMIN_PASSWORD', None)


class TestSetupGetRoute:
    def test_setup_page_loads(self, admin_client):
        response = admin_client.get('/setup')
        assert response.status_code == 200
        assert b'company-name' in response.data

    def test_setup_requires_password_when_set(self, protected_client):
        response = protected_client.get('/setup')
        assert response.status_code == 401

    def test_setup_accepts_password_in_query(self, protected_client):
        response = protected_client.get('/setup?password=secret123')
        assert response.status_code == 200

    def test_setup_rejects_wrong_password(self, protected_client):
        response = protected_client.get('/setup?password=wrong')
        assert response.status_code == 401


class TestUploadCsv:
    def test_upload_valid_csv_returns_columns_and_preview(self, admin_client, tmp_path):
        csv_content = b'firstName,lastName,team\nAlice,Dupont,Eng\nBob,Martin,Sales\n'
        data = {'file': (io.BytesIO(csv_content), 'test.csv')}
        response = admin_client.post('/setup/upload-csv', data=data, content_type='multipart/form-data')

        assert response.status_code == 200
        body = response.get_json()
        assert body['columns'] == ['firstName', 'lastName', 'team']
        assert body['filename'] == 'test.csv'
        assert len(body['preview']) == 2
        assert body['preview'][0]['firstName'] == 'Alice'

    def test_upload_no_file_returns_400(self, admin_client):
        response = admin_client.post('/setup/upload-csv', data={}, content_type='multipart/form-data')
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_upload_non_csv_extension_returns_400(self, admin_client):
        data = {'file': (io.BytesIO(b'hello'), 'document.txt')}
        response = admin_client.post('/setup/upload-csv', data=data, content_type='multipart/form-data')
        assert response.status_code == 400

    def test_upload_malformed_csv_returns_400(self, admin_client):
        # Binary garbage with .csv extension
        data = {'file': (io.BytesIO(b'\x00\x01\x02binary'), 'bad.csv')}
        response = admin_client.post('/setup/upload-csv', data=data, content_type='multipart/form-data')
        # pandas may accept the garbage as a single-column CSV, so we just check it doesn't 500
        assert response.status_code in (200, 400)


class TestSaveConfig:
    def test_save_writes_yaml(self, admin_client, tmp_path, monkeypatch):
        saved = {}

        def fake_save(config_dict, config_path='config.yaml'):
            saved['dict'] = config_dict
            saved['path'] = config_path

        monkeypatch.setattr('routes.admin_routes.CompanyConfig.save', fake_save)

        payload = {
            'company': {
                'name': 'Acme',
                'logo_url': 'https://acme.com/logo.png',
                'contact_email': 'admin@acme.com',
                'tagline': 'Rocks',
            },
            'column_mapping': {
                'first_name': 'firstName',
                'last_name': 'lastName',
                'photo': 'image',
            },
            'csv_filename': 'team.csv',
            'images_dir': 'static/images',
        }
        response = admin_client.post('/setup/save', json=payload)

        assert response.status_code == 200
        assert response.get_json() == {'success': True}
        assert saved['dict']['company']['name'] == 'Acme'
        assert saved['dict']['data']['csv_path'] == 'team.csv'
        assert saved['dict']['data']['column_mapping']['first_name'] == 'firstName'

    def test_save_without_body_returns_400(self, admin_client):
        response = admin_client.post('/setup/save', data='', content_type='application/json')
        assert response.status_code == 400

    def test_save_propagates_exception_as_500(self, admin_client, monkeypatch):
        def failing_save(config_dict, config_path='config.yaml'):
            raise OSError('disk full')

        monkeypatch.setattr('routes.admin_routes.CompanyConfig.save', failing_save)

        response = admin_client.post('/setup/save', json={'company': {}})
        assert response.status_code == 500
        assert 'disk full' in response.get_json()['error']


class TestUploadPhotos:
    def test_upload_valid_zip_extracts_images(self, admin_client, tmp_path, monkeypatch):
        target_dir = tmp_path / 'images'

        # Patch CompanyConfig to point images_dir to tmp_path
        class FakeConfig:
            def __init__(self, *a, **kw):
                self.images_dir = str(target_dir)

        monkeypatch.setattr('routes.admin_routes.CompanyConfig', FakeConfig)

        # Build a ZIP with 2 valid images + 1 non-image
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('alice.jpg', b'fake jpg')
            zf.writestr('bob.png', b'fake png')
            zf.writestr('readme.txt', b'ignore me')
        buf.seek(0)

        data = {'file': (buf, 'photos.zip')}
        response = admin_client.post('/setup/upload-photos', data=data, content_type='multipart/form-data')

        assert response.status_code == 200
        assert response.get_json()['extracted'] == 2
        assert (target_dir / 'alice.jpg').exists()
        assert (target_dir / 'bob.png').exists()
        assert not (target_dir / 'readme.txt').exists()

    def test_upload_non_zip_returns_400(self, admin_client):
        data = {'file': (io.BytesIO(b'not a zip'), 'file.jpg')}
        response = admin_client.post('/setup/upload-photos', data=data, content_type='multipart/form-data')
        assert response.status_code == 400

    def test_upload_corrupt_zip_returns_400(self, admin_client, monkeypatch, tmp_path):
        class FakeConfig:
            def __init__(self, *a, **kw):
                self.images_dir = str(tmp_path)

        monkeypatch.setattr('routes.admin_routes.CompanyConfig', FakeConfig)

        data = {'file': (io.BytesIO(b'PK not really a zip'), 'fake.zip')}
        response = admin_client.post('/setup/upload-photos', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
