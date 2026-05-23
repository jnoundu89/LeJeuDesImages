"""Integration tests for multi-dataset runtime: cookie switching, first-run empty state."""
import yaml

from app import create_app
from models.dataset_registry import DATASET_COOKIE


def _write_multi_dataset_config(tmp_path) -> str:
    csv_a = tmp_path / 'acme.csv'
    csv_a.write_text(
        'firstName,lastName,photo_path,team,jobTitle,company,sex\n'
        'Alice,Dupont,alice.jpg,Eng,Dev,Acme,F\n'
    )
    csv_b = tmp_path / 'client_x.csv'
    csv_b.write_text(
        'firstName,lastName,photo_path,team,jobTitle,company,sex\n'
        'Zoe,Roe,zoe.jpg,HR,Lead,ClientX,F\n'
    )

    mapping = {
        'first_name': 'firstName', 'last_name': 'lastName', 'photo': 'photo_path',
        'team': 'team', 'job_title': 'jobTitle', 'company': 'company', 'sex': 'sex',
    }

    cfg_path = tmp_path / 'config.yaml'
    cfg_path.write_text(yaml.dump({
        'app': {'contact_email': 'x@y.com', 'default_dataset': 'acme'},
        'datasets': {
            'acme': {
                'company': {'name': 'Acme Corp'},
                'data': {
                    'csv_path': str(csv_a),
                    'scores_db_path': str(tmp_path / 'acme_scores.json'),
                    'images_dir': str(tmp_path / 'acme_photos'),
                    'column_mapping': mapping,
                },
            },
            'client_x': {
                'company': {'name': 'Client X'},
                'data': {
                    'csv_path': str(csv_b),
                    'scores_db_path': str(tmp_path / 'client_x_scores.json'),
                    'images_dir': str(tmp_path / 'client_x_photos'),
                    'column_mapping': mapping,
                },
            },
        },
    }))
    return str(cfg_path)


class TestDatasetCookieSwitching:
    def test_dataset_cookie_selects_active_dataset(self, tmp_path):
        app = create_app(_write_multi_dataset_config(tmp_path))
        client = app.test_client()

        # Default (no cookie) → Acme branding injected
        resp = client.get('/about')
        assert resp.status_code == 200
        assert b'Acme Corp' in resp.data

        # With dataset cookie pointing to client_x → Client X branding
        client.set_cookie(DATASET_COOKIE, 'client_x')
        resp = client.get('/about')
        assert resp.status_code == 200
        assert b'Client X' in resp.data

    def test_set_dataset_endpoint_sets_cookie_and_clears_session(self, tmp_path):
        app = create_app(_write_multi_dataset_config(tmp_path))
        client = app.test_client()

        # Plant some session state that should be wiped on switch
        with client.session_transaction() as sess:
            sess['data_id'] = 42
            sess['user_id'] = 1

        resp = client.get('/dataset/client_x', follow_redirects=False)
        assert resp.status_code == 302

        # Cookie is set on the response
        cookies = resp.headers.getlist('Set-Cookie')
        assert any(DATASET_COOKIE + '=client_x' in c for c in cookies)

        # Session was cleared (data_id gone)
        with client.session_transaction() as sess:
            assert 'data_id' not in sess

    def test_set_dataset_unknown_id_is_ignored(self, tmp_path):
        app = create_app(_write_multi_dataset_config(tmp_path))
        client = app.test_client()

        resp = client.get('/dataset/ghost', follow_redirects=False)
        assert resp.status_code == 302
        cookies = resp.headers.getlist('Set-Cookie')
        # No dataset cookie set for unknown id
        assert not any(DATASET_COOKIE + '=ghost' in c for c in cookies)


class TestHeaderDropdown:
    def test_dropdown_rendered_with_multiple_datasets(self, tmp_path):
        app = create_app(_write_multi_dataset_config(tmp_path))
        client = app.test_client()

        resp = client.get('/about')
        assert b'app-dataset-select' in resp.data
        assert b'<option value="acme"' in resp.data
        assert b'<option value="client_x"' in resp.data

    def test_dropdown_highlights_current_dataset(self, tmp_path):
        app = create_app(_write_multi_dataset_config(tmp_path))
        client = app.test_client()
        client.set_cookie(DATASET_COOKIE, 'client_x')

        resp = client.get('/about')
        assert b'<option value="client_x" selected' in resp.data

    def test_dropdown_not_rendered_with_single_dataset(self, tmp_path):
        # Build a dedicated app with a guaranteed-single-dataset config so
        # this test doesn't accidentally read whatever the developer's
        # local config.yaml currently looks like (the session-scoped `app`
        # fixture caches that across runs).
        cfg = tmp_path / 'one.yaml'
        cfg.write_text(
            'app:\n'
            '  contact_email: test@example.com\n'
            '  default_dataset: only\n'
            'datasets:\n'
            '  only:\n'
            '    company:\n'
            '      name: OnlyCo\n'
            '    data:\n'
            '      csv_path: tests/fixtures/test_team.csv\n'
            '      images_dir: static/images\n'
            '      scores_db_path: ' + str(tmp_path / 'scores.json') + '\n'
            '      column_mapping:\n'
            '        first_name: firstName\n'
            '        last_name: lastName\n'
            '        photo: image_path\n'
            '        team: department_name\n'
            '        job_title: jobTitle\n'
            '        company: legalEntity_name\n'
            '        sex: sex\n'
        )
        app = create_app(str(cfg))
        client = app.test_client()
        resp = client.get('/about')
        # dataset switcher block should be absent (only 1 dataset)
        assert b'app-dataset-select' not in resp.data


class TestFirstRunEmptyState:
    def test_empty_registry_redirects_root_to_setup(self, tmp_path):
        # No config file at all → registry is empty
        missing_path = str(tmp_path / 'no_such.yaml')
        app = create_app(missing_path)
        client = app.test_client()

        resp = client.get('/', follow_redirects=False)
        assert resp.status_code == 302
        assert '/setup' in resp.headers['Location']

    def test_empty_registry_allows_setup_page(self, tmp_path):
        missing_path = str(tmp_path / 'no_such.yaml')
        app = create_app(missing_path)
        client = app.test_client()

        resp = client.get('/setup', follow_redirects=False)
        assert resp.status_code == 200

    def test_empty_registry_allows_lang_switch(self, tmp_path):
        missing_path = str(tmp_path / 'no_such.yaml')
        app = create_app(missing_path)
        client = app.test_client()

        resp = client.get('/lang/en', follow_redirects=False)
        assert resp.status_code == 302
        # Should not be redirected to /setup — just the lang cookie redirect
        assert '/setup' not in resp.headers.get('Location', '')
