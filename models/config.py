from pathlib import Path

import yaml

REQUIRED_FIELDS = {'first_name', 'last_name', 'photo', 'team', 'job_title', 'company', 'sex'}
OPTIONAL_FIELDS = {'birth_date', 'contract_start', 'manager_name'}


class CompanyConfig:
    def __init__(self, config_path: str = 'config.yaml'):
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f'Config file not found: {config_path}')

        with open(path, encoding='utf-8') as f:
            raw = yaml.safe_load(f)

        self._company = raw.get('company', {})
        self._data = raw.get('data', {})
        self._column_mapping = self._data.get('column_mapping', {})

        self._validate()

    def _validate(self):
        missing = REQUIRED_FIELDS - set(self._column_mapping.keys())
        if missing:
            raise ValueError(f'Missing required column mappings: {missing}')

        if not self._data.get('csv_path'):
            raise ValueError('data.csv_path is required')

    # -- Company accessors --

    @property
    def company_name(self) -> str:
        return self._company.get('name', 'My Company')

    @property
    def logo_url(self) -> str:
        return self._company.get('logo_url', '')

    @property
    def contact_email(self) -> str:
        return self._company.get('contact_email', '')

    @property
    def tagline(self) -> str:
        return self._company.get('tagline', '')

    # -- Data accessors --

    @property
    def csv_path(self) -> str:
        return self._data['csv_path']

    @property
    def images_dir(self) -> str:
        return self._data.get('images_dir', 'static/images')

    @property
    def column_mapping(self) -> dict:
        return dict(self._column_mapping)

    def reverse_mapping(self) -> dict:
        """Return {csv_column: canonical_name} for renaming DataFrame columns."""
        return {v: k for k, v in self._column_mapping.items()}

    @staticmethod
    def save(config_dict: dict, config_path: str = 'config.yaml'):
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
