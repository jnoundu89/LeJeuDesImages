"""Integration tests for /setup admin API endpoints (multi-dataset CRUD)."""
import io
import json
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
            # HTML GET → 302 redirect to the login form (no JSON 401 body).
            resp = isolated_client.get('/setup')
            assert resp.status_code == 302
            assert '/setup/login' in resp.headers.get('Location', '')
            # JSON/non-GET callers still get the terser 401 response.
            json_resp = isolated_client.get('/setup', headers={'Accept': 'application/json'})
            assert json_resp.status_code == 401
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

    def test_new_mode_persists_primary_color_and_settings(self, isolated_app, isolated_client):
        self._upload_csv(isolated_client, 'branded.csv')
        payload = {
            'mode': 'new',
            'id': 'branded',
            'company': {
                'name': 'Branded',
                'logo_url': '',
                'tagline': '',
                'primary_color': '#ff5733',
            },
            'settings': {'hide_unavailable_modes': True},
            'column_mapping': self._valid_mapping(),
            'csv_filename': 'branded.csv',
        }
        resp = isolated_client.post('/setup/save', json=payload)
        assert resp.status_code == 200, resp.get_json()

        ds = isolated_app.config['DATASET_REGISTRY'].get('branded')
        assert ds.config.primary_color == '#FF5733'  # normalised to uppercase
        assert ds.config.hide_unavailable_modes is True

    def test_save_falls_back_to_default_color_when_invalid(self, isolated_app, isolated_client):
        self._upload_csv(isolated_client, 'badcolor.csv')
        payload = {
            'mode': 'new',
            'id': 'badcolor',
            'company': {'name': 'BC', 'primary_color': 'not-a-color'},
            'column_mapping': self._valid_mapping(),
            'csv_filename': 'badcolor.csv',
        }
        resp = isolated_client.post('/setup/save', json=payload)
        assert resp.status_code == 200
        # Invalid hex → back to default indigo, not persisted as garbage.
        assert isolated_app.config['DATASET_REGISTRY'].get('badcolor').config.primary_color == '#4F46E5'

    def test_save_persists_palette_choice(self, isolated_app, isolated_client):
        self._upload_csv(isolated_client, 'palette.csv')
        payload = {
            'mode': 'new',
            'id': 'warm_co',
            'company': {
                'name': 'Warm',
                'primary_color': '#B45309',
                'palette': 'warm',
            },
            'column_mapping': self._valid_mapping(),
            'csv_filename': 'palette.csv',
        }
        resp = isolated_client.post('/setup/save', json=payload)
        assert resp.status_code == 200, resp.get_json()
        ds = isolated_app.config['DATASET_REGISTRY'].get('warm_co')
        assert ds.config.palette == 'warm'
        assert ds.config.primary_color == '#B45309'

    def test_save_rejects_unknown_palette_silently(self, isolated_app, isolated_client):
        self._upload_csv(isolated_client, 'weird.csv')
        payload = {
            'mode': 'new',
            'id': 'weird_co',
            'company': {'name': 'W', 'palette': 'rainbow_unicorn'},
            'column_mapping': self._valid_mapping(),
            'csv_filename': 'weird.csv',
        }
        resp = isolated_client.post('/setup/save', json=payload)
        assert resp.status_code == 200
        # Unknown palette → silently clamped to default.
        assert isolated_app.config['DATASET_REGISTRY'].get('weird_co').config.palette == 'corporate'

    def test_save_accepts_new_theme_payload(self, isolated_app, isolated_client):
        """Phase 3 wizard sends `theme: {palette, overrides}` — the
        preferred shape. Overrides make it to the stored DatasetTheme."""
        self._upload_csv(isolated_client, 'themed.csv')
        payload = {
            'mode': 'new',
            'id': 'themed',
            'company': {'name': 'Themed Co'},
            'theme': {
                'palette': 'midnight',
                'overrides': {
                    'surface': '#3E4A7A',
                    'text-soft': '#C8D0F0',
                    'primary': '#FF4D4D',
                },
            },
            'column_mapping': self._valid_mapping(),
            'csv_filename': 'themed.csv',
        }
        resp = isolated_client.post('/setup/save', json=payload)
        assert resp.status_code == 200, resp.get_json()

        ds = isolated_app.config['DATASET_REGISTRY'].get('themed')
        assert ds.config.theme.palette == 'midnight'
        assert ds.config.theme.overrides == {
            'surface': '#3E4A7A',
            'text-soft': '#C8D0F0',
            'primary': '#FF4D4D',
        }
        assert ds.config.primary_color == '#FF4D4D'  # back-compat property

    def test_save_filters_unknown_override_keys(self, isolated_app, isolated_client):
        """A malicious payload with unknown/garbage tokens is cleaned,
        valid ones survive."""
        self._upload_csv(isolated_client, 'dirty.csv')
        payload = {
            'mode': 'new',
            'id': 'dirty',
            'company': {'name': 'Dirty'},
            'theme': {
                'palette': 'ocean',
                'overrides': {
                    'surface': '#1F548F',     # kept
                    'evil_key': 'javascript:alert(1)',  # dropped
                    'text': 'not-a-hex',      # dropped
                    'primary': '#FF5733',     # kept
                },
            },
            'column_mapping': self._valid_mapping(),
            'csv_filename': 'dirty.csv',
        }
        resp = isolated_client.post('/setup/save', json=payload)
        assert resp.status_code == 200, resp.get_json()
        overrides = isolated_app.config['DATASET_REGISTRY'].get('dirty').config.theme.overrides
        assert overrides == {'surface': '#1F548F', 'primary': '#FF5733'}

    def test_save_accepts_explicit_background_effect(self, isolated_app, isolated_client):
        """Wizard can request fireworks bg on a non-legacy palette
        — gets persisted as theme.background_effect=fireworks."""
        self._upload_csv(isolated_client, 'fwbg.csv')
        resp = isolated_client.post('/setup/save', json={
            'mode': 'new',
            'id': 'fwbg',
            'company': {'name': 'FW BG'},
            'theme': {
                'palette': 'midnight',
                'overrides': {},
                'background_effect': 'fireworks',
            },
            'column_mapping': self._valid_mapping(),
            'csv_filename': 'fwbg.csv',
        })
        assert resp.status_code == 200, resp.get_json()
        ds = isolated_app.config['DATASET_REGISTRY'].get('fwbg')
        assert ds.config.theme.palette == 'midnight'
        assert ds.config.theme.background_effect == 'fireworks'
        assert ds.config.theme.background_effect_explicit == 'fireworks'

    def test_save_drops_invalid_background_effect(self, isolated_app, isolated_client):
        """Garbage values for background_effect are silently dropped
        — the dataset still saves, just with the palette default."""
        self._upload_csv(isolated_client, 'badbg.csv')
        resp = isolated_client.post('/setup/save', json={
            'mode': 'new',
            'id': 'badbg',
            'company': {'name': 'Bad BG'},
            'theme': {
                'palette': 'midnight',
                'background_effect': 'lasers',  # nope
            },
            'column_mapping': self._valid_mapping(),
            'csv_filename': 'badbg.csv',
        })
        assert resp.status_code == 200, resp.get_json()
        ds = isolated_app.config['DATASET_REGISTRY'].get('badbg')
        assert ds.config.theme.background_effect == 'nasa'  # midnight default
        assert ds.config.theme.background_effect_explicit is None

    def test_edit_preserves_theme_overrides(self, isolated_app, isolated_client):
        """Editing a dataset through the new payload preserves previously
        saved overrides + adds new ones."""
        self._upload_csv(isolated_client, 'edit_themed.csv')
        # First create with overrides
        resp = isolated_client.post('/setup/save', json={
            'mode': 'new',
            'id': 'edit_themed',
            'company': {'name': 'Edit Themed'},
            'theme': {'palette': 'forest', 'overrides': {'surface': '#265A47'}},
            'column_mapping': self._valid_mapping(),
            'csv_filename': 'edit_themed.csv',
        })
        assert resp.status_code == 200

        # Then edit with a different override set
        resp = isolated_client.post('/setup/save', json={
            'mode': 'edit',
            'id': 'edit_themed',
            'company': {'name': 'Edit Themed'},
            'theme': {
                'palette': 'forest',
                'overrides': {'surface': '#2F6B55', 'primary': '#22C55E'},
            },
            'column_mapping': self._valid_mapping(),
            'csv_filename': '',
        })
        assert resp.status_code == 200, resp.get_json()

        overrides = isolated_app.config['DATASET_REGISTRY'].get('edit_themed').config.theme.overrides
        assert overrides == {'surface': '#2F6B55', 'primary': '#22C55E'}


class TestThemePresetRoutes:
    """Apply / delete saved theme presets without going through the
    main /setup/save flow. Lets the admin flip between Light and Dark
    in one click."""

    def _seed(self, isolated_client):
        """Save a dataset with two presets pre-staked."""
        csv = b'firstName,lastName,photo_path,team,jobTitle,company,sex\nA,B,a.jpg,T,J,Co,F\n'
        isolated_client.post(
            '/setup/upload-csv',
            data={'file': (io.BytesIO(csv), 'preset.csv')},
            content_type='multipart/form-data',
        )
        resp = isolated_client.post('/setup/save', json={
            'mode': 'new',
            'id': 'presetds',
            'company': {'name': 'PresetDS'},
            'theme': {
                'palette': 'slate',
                'overrides': {'primary': '#1ADC77', 'bg': '#041E42'},  # Dark active
                'presets': {
                    'Light': {
                        'palette': 'slate',
                        'overrides': {'primary': '#3A61F7', 'bg': '#F8F9FB'},
                    },
                    'Dark': {
                        'palette': 'slate',
                        'overrides': {'primary': '#1ADC77', 'bg': '#041E42'},
                    },
                },
            },
            'column_mapping': {
                'first_name': 'firstName', 'last_name': 'lastName',
                'photo': 'photo_path', 'team': 'team', 'job_title': 'jobTitle',
                'company': 'company', 'sex': 'sex',
            },
            'csv_filename': 'preset.csv',
        })
        assert resp.status_code == 200, resp.get_json()

    def test_apply_replaces_active_theme(self, isolated_app, isolated_client):
        self._seed(isolated_client)
        resp = isolated_client.post('/setup/presetds/theme/preset/Light/apply')
        assert resp.status_code == 200, resp.get_json()

        ds = isolated_app.config['DATASET_REGISTRY'].get('presetds')
        # Active theme now mirrors the Light preset.
        assert ds.config.theme.overrides == {'primary': '#3A61F7', 'bg': '#F8F9FB'}
        # Both presets remain available for further switching.
        assert set(ds.config.theme.presets.keys()) == {'Light', 'Dark'}

    def test_apply_unknown_preset_returns_404(self, isolated_app, isolated_client):
        self._seed(isolated_client)
        resp = isolated_client.post('/setup/presetds/theme/preset/Sepia/apply')
        assert resp.status_code == 404

    def test_apply_unknown_dataset_returns_404(self, isolated_client):
        resp = isolated_client.post('/setup/ghost/theme/preset/Light/apply')
        assert resp.status_code == 404

    def test_delete_removes_preset_keeps_active(self, isolated_app, isolated_client):
        self._seed(isolated_client)
        # Active theme = Dark equivalents from _seed.
        resp = isolated_client.post('/setup/presetds/theme/preset/Light/delete')
        assert resp.status_code == 200, resp.get_json()

        ds = isolated_app.config['DATASET_REGISTRY'].get('presetds')
        # Active theme is unchanged.
        assert ds.config.theme.overrides == {'primary': '#1ADC77', 'bg': '#041E42'}
        # Light is gone, Dark survives.
        assert list(ds.config.theme.presets.keys()) == ['Dark']

    def test_apply_then_delete_workflow(self, isolated_app, isolated_client):
        self._seed(isolated_client)
        # Apply Light → deletes the Dark preset → verify both states stuck.
        isolated_client.post('/setup/presetds/theme/preset/Light/apply')
        isolated_client.post('/setup/presetds/theme/preset/Dark/delete')
        ds = isolated_app.config['DATASET_REGISTRY'].get('presetds')
        assert ds.config.theme.overrides == {'primary': '#3A61F7', 'bg': '#F8F9FB'}
        assert list(ds.config.theme.presets.keys()) == ['Light']


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


class TestUploadPhotosPending:
    """Pre-creation photo upload (NEW mode wizard step 4): photos
    land in uploads/pending_photos/ and the save handler later moves
    them into data/<id>/photos/ at finalisation."""

    def test_pending_zip_extracts_to_buffer(self, isolated_app, isolated_client, tmp_path):
        # Override the pending dir under tmp_path to avoid touching the
        # repo's uploads/ during tests.
        pending = tmp_path / 'pending_photos'
        isolated_app.config['UPLOAD_DIR'] = str(tmp_path)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('alice.jpg', b'fake jpg')
            zf.writestr('bob.png', b'fake png')
        buf.seek(0)

        resp = isolated_client.post(
            '/setup/upload-photos-pending',
            data={'file': (buf, 'photos.zip')},
            content_type='multipart/form-data',
        )
        assert resp.status_code == 200, resp.get_json()
        assert resp.get_json()['extracted'] == 2
        assert (pending / 'alice.jpg').exists()
        assert (pending / 'bob.png').exists()

    def test_save_in_new_mode_drains_pending_into_dataset(
        self, isolated_app, isolated_client, tmp_path
    ):
        # Seed 2 files in the pending buffer + a CSV in uploads/
        # so the wizard's save() pulls everything together.
        isolated_app.config['UPLOAD_DIR'] = str(tmp_path)
        pending = tmp_path / 'pending_photos'
        pending.mkdir(parents=True, exist_ok=True)
        (pending / 'alice.jpg').write_bytes(b'fake jpg')
        (pending / 'bob.png').write_bytes(b'fake png')

        # CSV upload (the save handler expects it under uploads/<filename>)
        csv = b'firstName,lastName,photo_path,team,jobTitle,company,sex\nA,B,alice.jpg,T,J,Co,F\n'
        up = isolated_client.post(
            '/setup/upload-csv',
            data={'file': (io.BytesIO(csv), 'fresh.csv')},
            content_type='multipart/form-data',
        )
        assert up.status_code == 200

        resp = isolated_client.post('/setup/save', json={
            'mode': 'new',
            'id': 'fromzip',
            'company': {'name': 'FromZip'},
            'column_mapping': {
                'first_name': 'firstName', 'last_name': 'lastName',
                'photo': 'photo_path', 'team': 'team', 'job_title': 'jobTitle',
                'company': 'company', 'sex': 'sex',
            },
            'csv_filename': 'fresh.csv',
        })
        assert resp.status_code == 200, resp.get_json()

        ds = isolated_app.config['DATASET_REGISTRY'].get('fromzip')
        images_dir = Path(ds.config.images_dir)
        # Both pending photos landed in the new dataset's photos dir.
        assert (images_dir / 'alice.jpg').exists()
        assert (images_dir / 'bob.png').exists()
        # And the buffer is empty after the move.
        assert list(pending.iterdir()) == []


class TestMissingPhotosWarning:
    """When the CSV references photo files that aren't actually
    present on disk, save() returns the list under
    response.warnings.missing_photos so the wizard can flag them."""

    def test_save_returns_empty_list_when_all_photos_present(
        self, isolated_app, isolated_client, tmp_path
    ):
        # Seed pending photos for both rows + matching CSV.
        isolated_app.config['UPLOAD_DIR'] = str(tmp_path)
        pending = tmp_path / 'pending_photos'
        pending.mkdir(parents=True, exist_ok=True)
        (pending / 'a.jpg').write_bytes(b'fake')
        (pending / 'b.jpg').write_bytes(b'fake')

        csv = (b'firstName,lastName,photo_path,team,jobTitle,company,sex\n'
               b'A,Aa,a.jpg,T,J,Co,F\n'
               b'B,Bb,b.jpg,T,J,Co,M\n')
        isolated_client.post(
            '/setup/upload-csv',
            data={'file': (io.BytesIO(csv), 'all.csv')},
            content_type='multipart/form-data',
        )
        resp = isolated_client.post('/setup/save', json={
            'mode': 'new',
            'id': 'allgood',
            'company': {'name': 'AllGood'},
            'column_mapping': {
                'first_name': 'firstName', 'last_name': 'lastName',
                'photo': 'photo_path', 'team': 'team', 'job_title': 'jobTitle',
                'company': 'company', 'sex': 'sex',
            },
            'csv_filename': 'all.csv',
        })
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['warnings']['missing_photos'] == []

    def test_save_flags_missing_photos(self, isolated_app, isolated_client, tmp_path):
        # CSV references three photos but only one is uploaded → two missing.
        isolated_app.config['UPLOAD_DIR'] = str(tmp_path)
        pending = tmp_path / 'pending_photos'
        pending.mkdir(parents=True, exist_ok=True)
        (pending / 'a.jpg').write_bytes(b'fake')

        csv = (b'firstName,lastName,photo_path,team,jobTitle,company,sex\n'
               b'A,Aa,a.jpg,T,J,Co,F\n'
               b'B,Bb,b.jpg,T,J,Co,M\n'
               b'C,Cc,output/photos/c.jpg,T,J,Co,F\n')
        isolated_client.post(
            '/setup/upload-csv',
            data={'file': (io.BytesIO(csv), 'gaps.csv')},
            content_type='multipart/form-data',
        )
        resp = isolated_client.post('/setup/save', json={
            'mode': 'new',
            'id': 'gaps',
            'company': {'name': 'Gaps'},
            'column_mapping': {
                'first_name': 'firstName', 'last_name': 'lastName',
                'photo': 'photo_path', 'team': 'team', 'job_title': 'jobTitle',
                'company': 'company', 'sex': 'sex',
            },
            'csv_filename': 'gaps.csv',
        })
        assert resp.status_code == 200
        missing = resp.get_json()['warnings']['missing_photos']
        # b.jpg + c.jpg flagged. The Infolegale-style `output/photos/c.jpg`
        # entry is normalised to its bare filename in the warning.
        assert sorted(missing) == ['b.jpg', 'c.jpg']

    def test_employees_list_marks_rows_with_missing_photos(
        self, isolated_app, isolated_client, tmp_path
    ):
        # Build a dataset where one row has a photo that exists on
        # disk and another that doesn't; the GET /employees should
        # render the right placeholder per row.
        isolated_app.config['UPLOAD_DIR'] = str(tmp_path)
        pending = tmp_path / 'pending_photos'
        pending.mkdir(parents=True, exist_ok=True)
        (pending / 'present.jpg').write_bytes(b'fake')

        csv = (b'firstName,lastName,photo_path,team,jobTitle,company,sex\n'
               b'P,Resent,present.jpg,T,J,Co,F\n'
               b'M,Issing,output/photos/missing.jpg,T,J,Co,M\n')
        isolated_client.post(
            '/setup/upload-csv',
            data={'file': (io.BytesIO(csv), 'rows.csv')},
            content_type='multipart/form-data',
        )
        isolated_client.post('/setup/save', json={
            'mode': 'new',
            'id': 'rowdiff',
            'company': {'name': 'RowDiff'},
            'column_mapping': {
                'first_name': 'firstName', 'last_name': 'lastName',
                'photo': 'photo_path', 'team': 'team', 'job_title': 'jobTitle',
                'company': 'company', 'sex': 'sex',
            },
            'csv_filename': 'rows.csv',
        })

        resp = isolated_client.get('/setup/rowdiff/employees')
        assert resp.status_code == 200
        # The "missing" placeholder class only appears for the second row.
        assert b'employee-thumb placeholder missing' in resp.data


class TestEmployeeCrudRoutes:
    def test_list_page_shows_employees(self, isolated_client):
        resp = isolated_client.get('/setup/acme/employees')
        assert resp.status_code == 200
        assert b'Alice' in resp.data
        assert b'Dupont' in resp.data

    def test_list_unknown_dataset_redirects_to_setup(self, isolated_client):
        resp = isolated_client.get('/setup/ghost/employees', follow_redirects=False)
        assert resp.status_code == 302

    def test_new_employee_page_loads(self, isolated_client):
        resp = isolated_client.get('/setup/acme/employees/new')
        assert resp.status_code == 200
        assert b'field-first_name' in resp.data

    def test_edit_page_loads_with_existing_data(self, isolated_client):
        resp = isolated_client.get('/setup/acme/employees/0/edit')
        assert resp.status_code == 200
        assert b'Alice' in resp.data

    def test_edit_page_out_of_range_redirects(self, isolated_client):
        resp = isolated_client.get('/setup/acme/employees/999/edit', follow_redirects=False)
        assert resp.status_code == 302

    def test_create_employee_persists_to_csv(self, isolated_app, isolated_client):
        payload = {
            'first_name': 'Bob', 'last_name': 'Martin', 'photo': 'bob.jpg',
            'team': 'Sales', 'job_title': 'Rep', 'company': 'Acme', 'sex': 'M',
        }
        resp = isolated_client.post('/setup/acme/employees', json=payload)
        assert resp.status_code == 200, resp.get_json()

        employees = isolated_app.config['DATASET_REGISTRY'].get('acme').employee_data.get_all_employees()
        assert len(employees) == 2
        assert employees[1]['first_name'] == 'Bob'

        # Persisted to disk
        csv_path = isolated_app.config['DATASET_REGISTRY'].get('acme').config.csv_path
        assert 'Bob,Martin' in Path(csv_path).read_text()

    def test_create_rejects_missing_required_field(self, isolated_client):
        payload = {'first_name': 'Bob'}  # missing everything else
        resp = isolated_client.post('/setup/acme/employees', json=payload)
        assert resp.status_code == 400

    def test_update_employee_persists(self, isolated_app, isolated_client):
        payload = {
            'first_name': 'Alicia', 'last_name': 'Dupont', 'photo': 'alice.jpg',
            'team': 'Platform', 'job_title': 'Dev', 'company': 'Acme', 'sex': 'F',
        }
        resp = isolated_client.post('/setup/acme/employees/0', json=payload)
        assert resp.status_code == 200

        emp = isolated_app.config['DATASET_REGISTRY'].get('acme').employee_data.get_by_index(0)
        assert emp['first_name'] == 'Alicia'
        assert emp['team'] == 'Platform'

    def test_update_out_of_range_returns_404(self, isolated_client):
        resp = isolated_client.post('/setup/acme/employees/999', json={'first_name': 'X'})
        assert resp.status_code == 404

    def test_delete_employee_persists(self, isolated_app, isolated_client):
        resp = isolated_client.post('/setup/acme/employees/0/delete')
        assert resp.status_code == 200

        employees = isolated_app.config['DATASET_REGISTRY'].get('acme').employee_data.get_all_employees()
        assert len(employees) == 0

    def test_delete_out_of_range_returns_404(self, isolated_client):
        resp = isolated_client.post('/setup/acme/employees/999/delete')
        assert resp.status_code == 404

    def test_upload_photo_saves_and_updates_record(self, isolated_app, isolated_client):
        # Build a real 2x2 JPEG so the Pillow validator accepts it.
        from PIL import Image as _PILImage
        buf = io.BytesIO()
        _PILImage.new('RGB', (2, 2), color=(255, 0, 0)).save(buf, format='JPEG')
        buf.seek(0)

        resp = isolated_client.post(
            '/setup/acme/employees/0/photo',
            data={'file': (buf, 'new.jpg')},
            content_type='multipart/form-data',
        )
        assert resp.status_code == 200, resp.get_json()

        # Response now ships the canonical `/photos/<filename>` URL so
        # the client can drop it straight into <img src>.
        photo_url = resp.get_json()['photo']
        assert photo_url.startswith('/photos/')
        assert photo_url.endswith('.jpg')

        # Employee's photo field is updated to the new (normalised) URL.
        emp = isolated_app.config['DATASET_REGISTRY'].get('acme').employee_data.get_by_index(0)
        assert emp['photo'] == photo_url

        # The bare filename still exists at the expected disk location.
        photo_filename = photo_url.removeprefix('/photos/')
        images_dir = Path(isolated_app.config['DATASET_REGISTRY'].get('acme').config.images_dir)
        assert (images_dir / photo_filename).exists()

    def test_upload_photo_rejects_fake_jpeg_bytes(self, isolated_client):
        # Bytes pretending to be a JPEG are rejected by the magic-number check.
        resp = isolated_client.post(
            '/setup/acme/employees/0/photo',
            data={'file': (io.BytesIO(b'fake jpg'), 'evil.jpg')},
            content_type='multipart/form-data',
        )
        assert resp.status_code == 400
        assert 'oversize' in resp.get_json()['error'].lower() or 'invalid' in resp.get_json()['error'].lower()

    def test_upload_photo_rejects_bad_extension(self, isolated_client):
        resp = isolated_client.post(
            '/setup/acme/employees/0/photo',
            data={'file': (io.BytesIO(b'x'), 'file.txt')},
            content_type='multipart/form-data',
        )
        assert resp.status_code == 400


class TestCleanupPhotos:
    def test_lists_orphans_without_deleting_by_default(self, isolated_app, isolated_client, tmp_path):
        # Seed the dataset images_dir with one file the CSV references + one orphan
        ds = isolated_app.config['DATASET_REGISTRY'].get('acme')
        images_dir = Path(ds.config.images_dir)
        images_dir.mkdir(parents=True, exist_ok=True)
        (images_dir / 'referenced.jpg').write_bytes(b'ok')
        (images_dir / 'orphan.jpg').write_bytes(b'orphan')

        # Make the first employee's photo point at the referenced file.
        ds.employee_data.update_at_index(0, {'photo': 'referenced.jpg'})
        ds.employee_data.save()

        resp = isolated_client.post('/setup/acme/cleanup-photos', json={})
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'orphan.jpg' in body['orphans']
        assert 'referenced.jpg' not in body['orphans']
        assert body['removed'] == 0
        # Preview must NOT delete.
        assert (images_dir / 'orphan.jpg').exists()

    def test_confirm_true_deletes_orphans(self, isolated_app, isolated_client):
        ds = isolated_app.config['DATASET_REGISTRY'].get('acme')
        images_dir = Path(ds.config.images_dir)
        images_dir.mkdir(parents=True, exist_ok=True)
        (images_dir / 'referenced.jpg').write_bytes(b'ok')
        (images_dir / 'orphan.jpg').write_bytes(b'orphan')
        ds.employee_data.update_at_index(0, {'photo': 'referenced.jpg'})
        ds.employee_data.save()

        resp = isolated_client.post('/setup/acme/cleanup-photos', json={'confirm': True})
        assert resp.status_code == 200
        assert resp.get_json()['removed'] == 1
        assert not (images_dir / 'orphan.jpg').exists()
        assert (images_dir / 'referenced.jpg').exists()


class TestExportImport:
    def test_export_returns_zip_with_manifest_and_csv(self, isolated_app, isolated_client):
        # Seed a photo so the archive contains a photos/ entry too.
        ds = isolated_app.config['DATASET_REGISTRY'].get('acme')
        images_dir = Path(ds.config.images_dir)
        images_dir.mkdir(parents=True, exist_ok=True)
        (images_dir / 'alice.jpg').write_bytes(b'\xff\xd8\xff\xe0')  # JPEG magic

        resp = isolated_client.get('/setup/acme/export')
        assert resp.status_code == 200
        assert resp.headers['Content-Type'] == 'application/zip'

        import zipfile as zipfile_mod
        zf = zipfile_mod.ZipFile(io.BytesIO(resp.data))
        names = zf.namelist()
        assert 'manifest.json' in names
        assert 'team.csv' in names
        assert 'photos/alice.jpg' in names

        manifest = json.loads(zf.read('manifest.json').decode('utf-8'))
        assert manifest['dataset_id'] == 'acme'
        assert 'company' in manifest['config']

    def test_import_from_exported_archive_creates_new_dataset(self, isolated_app, isolated_client):
        # Export first
        resp = isolated_client.get('/setup/acme/export')
        assert resp.status_code == 200
        archive = resp.data

        # Import under a fresh id
        resp = isolated_client.post(
            '/setup/import',
            data={
                'file': (io.BytesIO(archive), 'acme.zip'),
                'dataset_id': 'acme_clone',
            },
            content_type='multipart/form-data',
        )
        assert resp.status_code == 200, resp.get_json()

        registry = isolated_app.config['DATASET_REGISTRY']
        assert 'acme_clone' in registry.ids()
        cloned = registry.get('acme_clone')
        assert cloned.config.company_name == registry.get('acme').config.company_name

    def test_import_refuses_existing_id(self, isolated_client):
        resp = isolated_client.get('/setup/acme/export')
        archive = resp.data

        resp = isolated_client.post(
            '/setup/import',
            data={
                'file': (io.BytesIO(archive), 'acme.zip'),
                'dataset_id': 'acme',  # collides
            },
            content_type='multipart/form-data',
        )
        assert resp.status_code == 409

    def test_import_rejects_invalid_zip(self, isolated_client):
        resp = isolated_client.post(
            '/setup/import',
            data={
                'file': (io.BytesIO(b'not a zip'), 'bad.zip'),
                'dataset_id': 'wontmatter',
            },
            content_type='multipart/form-data',
        )
        assert resp.status_code == 400

    def test_theme_overrides_survive_export_import_roundtrip(self, isolated_app, isolated_client):
        """An admin's custom overrides shouldn't be lost on export+re-import."""
        # Seed the original dataset with a bespoke theme: midnight palette
        # + custom surface color + custom primary.
        csv = b'firstName,lastName,photo_path,team,jobTitle,company,sex\nZoe,Roe,z.jpg,HR,Mgr,ClientX,F\n'
        up = isolated_client.post(
            '/setup/upload-csv',
            data={'file': (io.BytesIO(csv), 'themed_for_rt.csv')},
            content_type='multipart/form-data',
        )
        assert up.status_code == 200
        resp = isolated_client.post('/setup/save', json={
            'mode': 'new',
            'id': 'themed_rt',
            'company': {'name': 'Themed RT'},
            'theme': {
                'palette': 'midnight',
                'overrides': {
                    'surface': '#5B6A9C',
                    'primary': '#FF4D4D',
                },
            },
            'column_mapping': {
                'first_name': 'firstName', 'last_name': 'lastName', 'photo': 'photo_path',
                'team': 'team', 'job_title': 'jobTitle', 'company': 'company', 'sex': 'sex',
            },
            'csv_filename': 'themed_for_rt.csv',
        })
        assert resp.status_code == 200, resp.get_json()

        # Export → same ZIP shape as the test above
        resp = isolated_client.get('/setup/themed_rt/export')
        assert resp.status_code == 200
        archive = resp.data

        # The manifest should embed the theme block so anything
        # round-tripping through this archive keeps the custom colors.
        import zipfile as zipfile_mod
        zf = zipfile_mod.ZipFile(io.BytesIO(archive))
        manifest = json.loads(zf.read('manifest.json').decode('utf-8'))
        assert manifest['config']['theme']['palette'] == 'midnight'
        assert manifest['config']['theme']['overrides'] == {
            'surface': '#5B6A9C',
            'primary': '#FF4D4D',
        }

        # Import under a fresh id and check the theme comes back intact.
        resp = isolated_client.post(
            '/setup/import',
            data={
                'file': (io.BytesIO(archive), 'themed_rt.zip'),
                'dataset_id': 'themed_rt_clone',
            },
            content_type='multipart/form-data',
        )
        assert resp.status_code == 200, resp.get_json()

        cloned = isolated_app.config['DATASET_REGISTRY'].get('themed_rt_clone')
        assert cloned.config.theme.palette == 'midnight'
        assert cloned.config.theme.overrides == {
            'surface': '#5B6A9C',
            'primary': '#FF4D4D',
        }


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
