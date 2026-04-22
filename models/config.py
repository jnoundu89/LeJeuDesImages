from pathlib import Path

import yaml

REQUIRED_FIELDS = {'first_name', 'last_name', 'photo', 'team', 'job_title', 'company', 'sex'}
OPTIONAL_FIELDS = {'birth_date', 'contract_start', 'manager_name'}


def _current_locale() -> str:
    """Return the active request locale, defaulting to 'fr' outside a request."""
    try:
        from flask import request  # imported lazily so tests without Flask still work
        return request.cookies.get('lang', 'fr')
    except Exception:
        return 'fr'


class DatasetConfig:
    """Config for a single dataset (employees CSV + photos + branding)."""

    def __init__(self, id: str, raw: dict):
        self.id = id
        self._company = raw.get('company', {})
        self._data = raw.get('data', {})
        self._column_mapping = self._data.get('column_mapping', {})
        self._validate()

    def _validate(self):
        missing = REQUIRED_FIELDS - set(self._column_mapping.keys())
        if missing:
            raise ValueError(
                f'Dataset {self.id!r}: Missing required column mappings: {missing}'
            )
        if not self._data.get('csv_path'):
            raise ValueError(f'Dataset {self.id!r}: data.csv_path is required')

    @property
    def company_name(self) -> str:
        return self._company.get('name', 'My Company')

    @property
    def logo_url(self) -> str:
        return self._company.get('logo_url', '')

    @property
    def tagline(self) -> str:
        """Tagline in the current Flask-Babel locale (FR fallback).

        Back-compat: accepts either a plain string or a ``{fr: ..., en: ...}``
        dict in ``config.yaml``.
        """
        return self.tagline_for(_current_locale())

    def tagline_for(self, locale: str) -> str:
        """Resolve the tagline string for a specific locale code."""
        raw = self._company.get('tagline', '')
        if isinstance(raw, dict):
            return raw.get(locale) or raw.get('fr') or raw.get('en') or next(iter(raw.values()), '')
        return raw or ''

    @property
    def taglines(self) -> dict:
        """Return the raw tagline mapping, normalised to {fr, en}.

        Stored value may be a plain string (legacy) or a partial dict. Missing
        locales fall back to whatever is available so the wizard can always
        prefill both inputs.
        """
        raw = self._company.get('tagline', '')
        if isinstance(raw, dict):
            fr = raw.get('fr') or raw.get('en') or ''
            en = raw.get('en') or raw.get('fr') or ''
            return {'fr': fr, 'en': en}
        return {'fr': raw or '', 'en': raw or ''}

    @property
    def csv_path(self) -> str:
        return self._data['csv_path']

    @property
    def images_dir(self) -> str:
        return self._data.get('images_dir', 'static/images')

    @property
    def scores_db_path(self) -> str:
        return self._data.get('scores_db_path', f'data/{self.id}/scores.json')

    @property
    def column_mapping(self) -> dict:
        return dict(self._column_mapping)

    def reverse_mapping(self) -> dict:
        """Return {csv_column: canonical_name} for renaming DataFrame columns."""
        return {v: k for k, v in self._column_mapping.items()}

    def to_dict(self) -> dict:
        return {
            'company': dict(self._company),
            'data': {
                'csv_path': self._data.get('csv_path', ''),
                'images_dir': self._data.get('images_dir', 'static/images'),
                'scores_db_path': self._data.get('scores_db_path', f'data/{self.id}/scores.json'),
                'column_mapping': dict(self._column_mapping),
            },
        }


class AppConfig:
    """Top-level config: app-wide settings + a registry of datasets.

    Supports the new multi-dataset format (top-level `app` + `datasets`) and
    auto-migrates the legacy single-dataset format (top-level `company` + `data`)
    into a single dataset with id="default".
    """

    def __init__(self, config_path: str = 'config.yaml'):
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f'Config file not found: {config_path}')

        with open(path, encoding='utf-8') as f:
            raw = yaml.safe_load(f) or {}

        if self._is_legacy_format(raw):
            raw = self._migrate_legacy(raw)

        self._app = raw.get('app', {})
        datasets_raw = raw.get('datasets') or {}
        self.datasets: dict[str, DatasetConfig] = {
            ds_id: DatasetConfig(ds_id, ds_raw)
            for ds_id, ds_raw in datasets_raw.items()
        }

    @staticmethod
    def _is_legacy_format(raw: dict) -> bool:
        return 'datasets' not in raw and ('company' in raw or 'data' in raw)

    @staticmethod
    def _migrate_legacy(raw: dict) -> dict:
        """Convert old single-dataset format to new multi-dataset format."""
        company = dict(raw.get('company', {}))
        contact_email = company.pop('contact_email', '')
        return {
            'app': {
                'contact_email': contact_email,
                'default_dataset': 'default',
            },
            'datasets': {
                'default': {
                    'company': company,
                    'data': dict(raw.get('data', {})),
                },
            },
        }

    @property
    def contact_email(self) -> str:
        return self._app.get('contact_email', '')

    @property
    def default_dataset_id(self) -> str:
        """Id of the dataset to load first. Falls back to the first dataset."""
        default = self._app.get('default_dataset')
        if default and default in self.datasets:
            return default
        return next(iter(self.datasets), '')

    def to_dict(self) -> dict:
        return {
            'app': {
                'contact_email': self.contact_email,
                'default_dataset': self.default_dataset_id,
            },
            'datasets': {
                ds_id: ds.to_dict() for ds_id, ds in self.datasets.items()
            },
        }

    @staticmethod
    def save(config_dict: dict, config_path: str = 'config.yaml'):
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)


class CompanyConfig:
    """Backwards-compatible view on the default dataset of an AppConfig.

    Deprecated: new code should use AppConfig + DatasetRegistry. This wrapper
    remains to keep legacy callers (app.py pre-Phase-3, admin_routes, tests)
    working without changes during the refactor.
    """

    def __init__(self, config_path: str = 'config.yaml'):
        self._app_config = AppConfig(config_path)
        default_id = self._app_config.default_dataset_id
        if not default_id:
            raise ValueError('No datasets configured')
        self._ds = self._app_config.datasets[default_id]

    @property
    def company_name(self) -> str:
        return self._ds.company_name

    @property
    def logo_url(self) -> str:
        return self._ds.logo_url

    @property
    def contact_email(self) -> str:
        return self._app_config.contact_email

    @property
    def tagline(self) -> str:
        return self._ds.tagline

    @property
    def csv_path(self) -> str:
        return self._ds.csv_path

    @property
    def images_dir(self) -> str:
        return self._ds.images_dir

    @property
    def column_mapping(self) -> dict:
        return self._ds.column_mapping

    def reverse_mapping(self) -> dict:
        return self._ds.reverse_mapping()

    @staticmethod
    def save(config_dict: dict, config_path: str = 'config.yaml'):
        AppConfig.save(config_dict, config_path)
