import pytest

from models.config import CompanyConfig


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
