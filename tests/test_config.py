import pytest

from models.config import AppConfig, CompanyConfig, DatasetConfig


class TestCompanyConfig:
    def test_load_valid_config(self, test_config):
        assert test_config.company_name == 'Test Corp'

    def test_missing_config_file_raises(self):
        with pytest.raises(FileNotFoundError):
            CompanyConfig('nonexistent.yaml')

    def test_missing_required_columns_raises(self):
        with pytest.raises(ValueError, match='Missing required column mappings'):
            CompanyConfig('tests/fixtures/test_config_invalid.yaml')

    def test_missing_csv_path_raises(self):
        with pytest.raises(ValueError, match='csv_path is required'):
            CompanyConfig('tests/fixtures/test_config_no_csv.yaml')

    def test_company_name(self, test_config):
        assert test_config.company_name == 'Test Corp'

    def test_logo_url(self, test_config):
        assert test_config.logo_url == 'https://example.com/logo.png'

    def test_contact_email(self, test_config):
        assert test_config.contact_email == 'test@example.com'

    def test_tagline(self, test_config):
        assert test_config.tagline == 'A test company tagline'

    def test_csv_path(self, test_config):
        assert test_config.csv_path == 'tests/fixtures/test_team.csv'

    def test_images_dir(self, test_config):
        assert test_config.images_dir == 'static/images'

    def test_column_mapping_returns_dict(self, test_config):
        mapping = test_config.column_mapping
        assert isinstance(mapping, dict)
        assert mapping['first_name'] == 'firstName'
        assert mapping['last_name'] == 'lastName'
        assert mapping['photo'] == 'image_path'

    def test_reverse_mapping(self, test_config):
        rev = test_config.reverse_mapping()
        assert rev['firstName'] == 'first_name'
        assert rev['lastName'] == 'last_name'
        assert rev['image_path'] == 'photo'
        assert rev['department_name'] == 'team'

    def test_column_mapping_is_copy(self, test_config):
        mapping = test_config.column_mapping
        mapping['first_name'] = 'MODIFIED'
        assert test_config.column_mapping['first_name'] == 'firstName'

    def test_defaults_for_missing_company_fields(self, tmp_path):
        config_path = tmp_path / 'minimal.yaml'
        config_path.write_text(
            'data:\n'
            '  csv_path: "dummy.csv"\n'
            '  column_mapping:\n'
            '    first_name: "fn"\n'
            '    last_name: "ln"\n'
            '    photo: "p"\n'
            '    team: "t"\n'
            '    job_title: "jt"\n'
            '    company: "c"\n'
            '    sex: "s"\n'
        )
        cfg = CompanyConfig(str(config_path))
        assert cfg.company_name == 'My Company'
        assert cfg.logo_url == ''
        assert cfg.contact_email == ''
        assert cfg.tagline == ''


def _minimal_mapping() -> dict:
    return {
        'first_name': 'fn',
        'last_name': 'ln',
        'photo': 'p',
        'team': 't',
        'job_title': 'jt',
        'company': 'c',
        'sex': 's',
    }


def _write_new_format(tmp_path, datasets: dict, app_settings: dict | None = None) -> str:
    import yaml
    payload = {
        'app': app_settings or {'contact_email': 'me@app.com', 'default_dataset': next(iter(datasets))},
        'datasets': datasets,
    }
    path = tmp_path / 'config.yaml'
    path.write_text(yaml.dump(payload))
    return str(path)


class TestAppConfig:
    def test_loads_new_format_with_multiple_datasets(self, tmp_path):
        datasets = {
            'acme': {
                'company': {'name': 'Acme'},
                'data': {'csv_path': 'data/acme/team.csv', 'column_mapping': _minimal_mapping()},
            },
            'client_x': {
                'company': {'name': 'Client X'},
                'data': {'csv_path': 'data/client_x/team.csv', 'column_mapping': _minimal_mapping()},
            },
        }
        path = _write_new_format(tmp_path, datasets)
        cfg = AppConfig(path)

        assert set(cfg.datasets.keys()) == {'acme', 'client_x'}
        assert cfg.datasets['acme'].company_name == 'Acme'
        assert cfg.datasets['client_x'].company_name == 'Client X'
        assert cfg.default_dataset_id == 'acme'
        assert cfg.contact_email == 'me@app.com'

    def test_default_dataset_falls_back_to_first_when_missing(self, tmp_path):
        datasets = {
            'one': {'data': {'csv_path': 'x.csv', 'column_mapping': _minimal_mapping()}},
        }
        path = _write_new_format(
            tmp_path, datasets, app_settings={'contact_email': '', 'default_dataset': 'nonexistent'}
        )
        cfg = AppConfig(path)
        assert cfg.default_dataset_id == 'one'

    def test_missing_config_file_raises(self):
        with pytest.raises(FileNotFoundError):
            AppConfig('nonexistent.yaml')

    def test_legacy_format_auto_migrated_to_default_dataset(self, tmp_path):
        """Legacy single-dataset YAML is migrated to a 'default' dataset in-memory."""
        legacy = tmp_path / 'legacy.yaml'
        legacy.write_text(
            'company:\n'
            '  name: "Test Corp"\n'
            '  logo_url: "https://example.com/logo.png"\n'
            '  contact_email: "test@example.com"\n'
            '  tagline: "A test company tagline"\n'
            '\n'
            'data:\n'
            '  csv_path: "tests/fixtures/test_team.csv"\n'
            '  images_dir: "static/images"\n'
            '  column_mapping:\n'
            '    first_name: "firstName"\n'
            '    last_name: "lastName"\n'
            '    photo: "image_path"\n'
            '    team: "department_name"\n'
            '    job_title: "jobTitle"\n'
            '    company: "legalEntity_name"\n'
            '    sex: "sex"\n',
            encoding='utf-8',
        )

        cfg = AppConfig(str(legacy))

        assert list(cfg.datasets.keys()) == ['default']
        assert cfg.default_dataset_id == 'default'
        assert cfg.contact_email == 'test@example.com'

        ds = cfg.datasets['default']
        assert ds.company_name == 'Test Corp'
        assert ds.logo_url == 'https://example.com/logo.png'
        assert ds.csv_path == 'tests/fixtures/test_team.csv'
        assert ds.column_mapping['first_name'] == 'firstName'

    def test_legacy_format_without_datasets_key_is_detected(self, tmp_path):
        path = tmp_path / 'legacy.yaml'
        path.write_text(
            'company:\n'
            '  name: "Old"\n'
            'data:\n'
            '  csv_path: "old.csv"\n'
            '  column_mapping:\n'
            + ''.join(f'    {k}: "{v}"\n' for k, v in _minimal_mapping().items())
        )
        cfg = AppConfig(str(path))
        assert 'default' in cfg.datasets
        assert cfg.datasets['default'].company_name == 'Old'

    def test_new_format_takes_precedence_over_legacy_keys(self, tmp_path):
        path = tmp_path / 'mixed.yaml'
        path.write_text(
            'datasets:\n'
            '  real:\n'
            '    data:\n'
            '      csv_path: "real.csv"\n'
            '      column_mapping:\n'
            + ''.join(f'        {k}: "{v}"\n' for k, v in _minimal_mapping().items())
            + 'company:\n'
            '  name: "Ignored"\n'
        )
        cfg = AppConfig(str(path))
        assert list(cfg.datasets.keys()) == ['real']


class TestDatasetConfig:
    def test_scores_db_path_defaults_under_data_dir(self):
        ds = DatasetConfig('acme', {'data': {'csv_path': 'x.csv', 'column_mapping': _minimal_mapping()}})
        assert ds.scores_db_path == 'data/acme/scores.json'

    def test_tagline_legacy_string_returned_as_is(self):
        ds = DatasetConfig(
            'acme',
            {
                'company': {'tagline': 'Plain old string'},
                'data': {'csv_path': 'x.csv', 'column_mapping': _minimal_mapping()},
            },
        )
        # Bare string tagline works for every locale.
        assert ds.tagline_for('fr') == 'Plain old string'
        assert ds.tagline_for('en') == 'Plain old string'
        assert ds.taglines == {'fr': 'Plain old string', 'en': 'Plain old string'}

    def test_tagline_dict_resolves_per_locale(self):
        ds = DatasetConfig(
            'acme',
            {
                'company': {'tagline': {'fr': 'Salut', 'en': 'Hello'}},
                'data': {'csv_path': 'x.csv', 'column_mapping': _minimal_mapping()},
            },
        )
        assert ds.tagline_for('fr') == 'Salut'
        assert ds.tagline_for('en') == 'Hello'
        assert ds.taglines == {'fr': 'Salut', 'en': 'Hello'}

    def test_tagline_partial_dict_falls_back_to_sibling_locale(self):
        ds = DatasetConfig(
            'acme',
            {
                'company': {'tagline': {'fr': 'Only FR'}},
                'data': {'csv_path': 'x.csv', 'column_mapping': _minimal_mapping()},
            },
        )
        # Missing EN borrows the FR string so the banner is never blank.
        assert ds.tagline_for('en') == 'Only FR'
        assert ds.tagline_for('fr') == 'Only FR'
        assert ds.taglines == {'fr': 'Only FR', 'en': 'Only FR'}

    def test_scores_db_path_from_config(self):
        ds = DatasetConfig(
            'acme',
            {
                'data': {
                    'csv_path': 'x.csv',
                    'scores_db_path': 'custom/path.json',
                    'column_mapping': _minimal_mapping(),
                }
            },
        )
        assert ds.scores_db_path == 'custom/path.json'

    def test_validation_error_includes_dataset_id(self):
        with pytest.raises(ValueError, match="Dataset 'broken'"):
            DatasetConfig('broken', {'data': {'csv_path': 'x.csv', 'column_mapping': {}}})

    def test_to_dict_round_trip(self):
        ds = DatasetConfig(
            'acme',
            {
                'company': {'name': 'Acme', 'logo_url': '/logo.png'},
                'data': {
                    'csv_path': 'x.csv',
                    'images_dir': 'custom/photos',
                    'column_mapping': _minimal_mapping(),
                },
            },
        )
        d = ds.to_dict()
        assert d['company']['name'] == 'Acme'
        assert d['data']['csv_path'] == 'x.csv'
        assert d['data']['images_dir'] == 'custom/photos'
        assert d['data']['column_mapping'] == _minimal_mapping()
