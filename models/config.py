import re
from pathlib import Path

import yaml

REQUIRED_FIELDS = {'first_name', 'last_name', 'photo', 'team', 'job_title', 'company', 'sex'}
OPTIONAL_FIELDS = {'birth_date', 'contract_start', 'manager_name'}

DEFAULT_PRIMARY_COLOR = '#4F46E5'
_HEX_COLOR_RE = re.compile(r'^#[0-9A-Fa-f]{6}$')

# Palette presets. The value stored on disk is one of these keys;
# static/design-tokens.css has matching `:root[data-palette="<key>"]`
# rules that override the neutral tokens while leaving --primary alone.
# `corporate` is the default (== unchanged neutral/Zinc look).
#
# Grouping, informational only — `PALETTE_KEYS` is a flat tuple that
# the admin UI can iterate.
#   Light   (9): corporate, slate, nordic, warm, sepia, sand, pastel, rose, mint
#   Dark    (7): midnight, charcoal, ocean, forest, plum, dark, noir
#   Special (1): legacy — opt-in cosmic theme that also unlocks bonus
#                effects (constellation upgrade, cosmic title glow,
#                card shine, fireworks bg, Konami code easter egg).
#                See static/legacy-theme.{css,js}.
PALETTE_KEYS = (
    'corporate', 'slate', 'nordic',
    'warm', 'sepia', 'sand',
    'pastel', 'rose', 'mint',
    'midnight', 'charcoal', 'ocean', 'forest', 'plum', 'dark', 'noir',
    'legacy',
)
LIGHT_PALETTE_KEYS = frozenset({
    'corporate', 'slate', 'nordic',
    'warm', 'sepia', 'sand',
    'pastel', 'rose', 'mint',
})
DARK_PALETTE_KEYS = frozenset({
    'midnight', 'charcoal', 'ocean', 'forest', 'plum', 'dark', 'noir',
    'legacy',  # rendered in the special group but resolves as dark
})
SPECIAL_PALETTE_KEYS = frozenset({'legacy'})
DEFAULT_PALETTE = 'corporate'


def normalise_color(value, fallback: str = DEFAULT_PRIMARY_COLOR) -> str:
    """Return a valid ``#RRGGBB`` hex color or the fallback."""
    if isinstance(value, str) and _HEX_COLOR_RE.match(value):
        return value.upper() if value.startswith('#') and len(value) == 7 else value
    return fallback


def normalise_palette(value, fallback: str = DEFAULT_PALETTE) -> str:
    """Return a known palette key or the fallback."""
    if isinstance(value, str) and value in PALETTE_KEYS:
        return value
    return fallback


# Tokens that the admin can override on top of a palette preset.
# Any other key in `theme.overrides` on disk is silently dropped to
# keep the config minimal and predictable.
EDITABLE_THEME_TOKENS = (
    # ---- Page surface + text ----
    'bg',             # page background
    'text',           # default body text
    'text-soft',      # descriptions, secondary paragraph text
    'text-muted',     # metadata (durations, labels, "DIFFICULTÉ" / "THÈMES" eyebrows)
    'border',         # separators, default outlines

    # ---- Generic surfaces (catch-all for anything not card/header/footer) ----
    'surface',        # filter bar, inputs, score-section, employee table, etc.
    'surface-2',      # hero, previews, elevated panels
    'surface-muted',  # tag pills, unavailable-mode preview bg

    # ---- Per-component overrides (each falls back to --surface / --text) ----
    'card-bg',        # mode cards + admin cards + game-page panels (`.stats`/`.center-content`/`.right-content`)
    'card-text',      # default text colour inside the cards above
    'header-bg',      # app + game header bar background
    'header-text',    # header bar text + nav link colour
    'footer-bg',      # `.app-footer` background
    'footer-text',    # footer text + links

    # ---- Brand accents ----
    'primary',        # buttons, focus, active link
    'success',        # secondary accent — mode-card strip end-stop, success states
)

# Animated background style. The first five values are particles.js
# library presets (vendored as JSON under static/vendor/presets/),
# pulled directly from the upstream demo at
#   https://vincentgarreau.com/particles.js/
# 'fireworks' is our custom canvas effect (static/fireworks-bg.js).
BACKGROUND_EFFECTS = (
    'nasa',       # twinkling white dots, no links — the user's reference
    'default',    # blue circles + connection lines
    'snow',       # falling snowflakes
    'bubble',     # rising semi-transparent circles
    'star',       # star-shaped particles drifting
    'fireworks',  # custom fireworks bursts
    'none',       # no animation at all — for admins who want a fully static page
)

# Aliases — old values that should resolve to a current key. Lets us
# rename presets without breaking configs already on disk.
_BACKGROUND_EFFECT_ALIASES = {
    # Pre-particles.js-library era stored 'particles' for the custom
    # constellation. The closest match in the new presets is 'nasa'
    # (small white dots with subtle motion).
    'particles': 'nasa',
}


def normalise_background_effect(value) -> str | None:
    """Return a known background-effect key, or None if invalid/unset.

    Returning None (rather than a default) is what lets the
    DatasetTheme property derive the right default per-palette
    (legacy → fireworks, anything else → nasa) when the field isn't
    explicitly set.
    """
    if not isinstance(value, str):
        return None
    if value in BACKGROUND_EFFECTS:
        return value
    if value in _BACKGROUND_EFFECT_ALIASES:
        return _BACKGROUND_EFFECT_ALIASES[value]
    return None


# Per-card visual flourishes. The 'shine' value enables a gold light
# sweep across cards on hover (the original legacy-only effect, now
# selectable on any palette via the wizard).
CARD_EFFECTS = ('none', 'shine')


def normalise_card_effect(value) -> str | None:
    """Return a known card-effect key, or None if invalid/unset.

    Returning None lets the DatasetTheme property derive the default
    from the palette ('shine' for legacy, 'none' otherwise) just like
    background_effect does.
    """
    if isinstance(value, str) and value in CARD_EFFECTS:
        return value
    return None


class DatasetTheme:
    """Theme for a single dataset: palette preset + per-token overrides.

    The palette is one of the 16 keys in :data:`PALETTE_KEYS`; it
    defines the default bg/surface/text triple. The admin can then
    override any of the tokens listed in :data:`EDITABLE_THEME_TOKENS`
    via ``overrides`` — e.g. ``{'surface': '#3E4A7A'}`` lifts the
    cards above the palette's default card color.

    Instances are immutable from the outside — constructed from a
    raw dict (disk or wizard payload), exposed via properties.
    """

    def __init__(self, raw: dict | None = None):
        raw = raw or {}
        self._palette = normalise_palette(raw.get('palette'))
        self._overrides = self._clean_overrides(raw.get('overrides'))
        self._background_effect = normalise_background_effect(raw.get('background_effect'))
        self._card_effect = normalise_card_effect(raw.get('card_effect'))
        self._presets = self._clean_presets(raw.get('presets'))

    @staticmethod
    def _clean_overrides(raw) -> dict[str, str]:
        """Keep only known tokens with valid hex values."""
        if not isinstance(raw, dict):
            return {}
        out: dict[str, str] = {}
        for key in EDITABLE_THEME_TOKENS:
            value = raw.get(key)
            if not value:
                continue
            if isinstance(value, str) and _HEX_COLOR_RE.match(value):
                out[key] = value.upper() if len(value) == 7 else value
        return out

    @classmethod
    def _clean_presets(cls, raw) -> dict[str, dict]:
        """Validate the saved-presets dict.

        Each entry: ``<name>: {palette, overrides, background_effect}``.
        Drops entries whose name isn't a non-empty string. Each entry's
        inner shape is normalised exactly like a top-level theme block
        (unknown palette → 'corporate', invalid hex overrides dropped,
        unknown background_effect → None). Empty / non-dict input
        returns ``{}``.
        """
        if not isinstance(raw, dict):
            return {}
        out: dict[str, dict] = {}
        for name, entry in raw.items():
            if not isinstance(name, str) or not name.strip():
                continue
            if not isinstance(entry, dict):
                continue
            cleaned: dict = {
                'palette': normalise_palette(entry.get('palette')),
                'overrides': cls._clean_overrides(entry.get('overrides')),
            }
            bg = normalise_background_effect(entry.get('background_effect'))
            if bg is not None:
                cleaned['background_effect'] = bg
            out[name.strip()] = cleaned
        return out

    @property
    def palette(self) -> str:
        return self._palette

    @property
    def overrides(self) -> dict[str, str]:
        return dict(self._overrides)

    @property
    def background_effect(self) -> str:
        """Resolved background-effect key.

        Returns the explicit value if set, else 'fireworks' for the
        legacy palette (back-compat with the original legacy bundle)
        or 'nasa' for everything else. Always one of
        :data:`BACKGROUND_EFFECTS`.
        """
        if self._background_effect is not None:
            return self._background_effect
        return 'fireworks' if self._palette == 'legacy' else 'nasa'

    @property
    def background_effect_explicit(self) -> str | None:
        """The raw stored value (None if defaulted by palette).

        Useful when persisting: we only want to write the field to
        disk when it's been explicitly set, not when it's been
        derived from the palette.
        """
        return self._background_effect

    @property
    def card_effect(self) -> str:
        """Resolved card hover/visual effect.

        Returns 'shine' for legacy palette by default (back-compat
        with the original legacy bundle that hardcoded the gold
        sweep), 'none' for everything else. The admin can override
        either way via the wizard.
        """
        if self._card_effect is not None:
            return self._card_effect
        return 'shine' if self._palette == 'legacy' else 'none'

    @property
    def card_effect_explicit(self) -> str | None:
        """The raw stored value (None if defaulted by palette)."""
        return self._card_effect

    @property
    def presets(self) -> dict[str, dict]:
        """Saved preset themes for this dataset, keyed by name.

        Each value is a normalised dict of ``{palette, overrides,
        background_effect?}`` — exactly the shape ``DatasetTheme(...)``
        accepts as a constructor argument. The wizard renders one row
        per entry with Apply / Delete actions; the apply route swaps
        the active theme to the preset's values without touching the
        rest of the dataset config.
        """
        # Deep copy so callers can't mutate our internal state.
        return {
            name: {**entry, 'overrides': dict(entry.get('overrides', {}))}
            for name, entry in self._presets.items()
        }

    @property
    def primary_color(self) -> str:
        """Primary brand color: the override if set, else the default."""
        return self._overrides.get('primary', DEFAULT_PRIMARY_COLOR)

    def resolved_overrides(self) -> dict[str, str]:
        """Overrides that should be inlined as CSS custom properties.

        Everything else is left to the palette's CSS rule to fill in.
        The caller (template) emits these as ``--<token>: <hex>`` in
        the ``<html>`` style attribute so they beat the palette.
        """
        return dict(self._overrides)

    def to_dict(self) -> dict:
        """Serialize to the YAML-friendly form (empty overrides omitted).

        ``background_effect`` is only persisted when explicitly set —
        when defaulted (palette-derived), we leave the key out so
        legacy users keep their auto-fireworks without the field
        appearing on disk.

        ``presets`` is only included when at least one preset has been
        saved, so a fresh dataset doesn't accumulate empty keys on disk.
        """
        payload: dict = {'palette': self._palette}
        if self._overrides:
            payload['overrides'] = dict(self._overrides)
        if self._background_effect is not None:
            payload['background_effect'] = self._background_effect
        if self._card_effect is not None:
            payload['card_effect'] = self._card_effect
        if self._presets:
            payload['presets'] = {
                name: {**entry, 'overrides': dict(entry.get('overrides', {}))}
                for name, entry in self._presets.items()
            }
        return payload

    @classmethod
    def from_raw_company(cls, company: dict) -> 'DatasetTheme':
        """Legacy path: build a theme from the pre-refactor fields.

        Older configs stored ``company.palette`` (string) and
        ``company.primary_color`` (hex) as flat keys. This keeps
        reading them seamlessly so nobody has to hand-migrate YAML.
        """
        raw: dict = {
            'palette': company.get('palette'),
            'overrides': {},
        }
        # Only treat primary_color as an override if it was explicitly
        # set to something other than the default — otherwise we'd
        # persist a noisy « override » equal to the default.
        legacy_primary = company.get('primary_color')
        if (
            isinstance(legacy_primary, str)
            and _HEX_COLOR_RE.match(legacy_primary)
            and legacy_primary.upper() != DEFAULT_PRIMARY_COLOR
        ):
            raw['overrides']['primary'] = legacy_primary
        return cls(raw)


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
        self._settings = raw.get('settings', {})
        self._column_mapping = self._data.get('column_mapping', {})
        # Theme: prefer the new nested `theme:` block. If absent, build
        # one from the legacy flat fields on `company` so old configs
        # keep working without a manual migration.
        raw_theme = raw.get('theme')
        if raw_theme is None:
            self._theme = DatasetTheme.from_raw_company(self._company)
        else:
            self._theme = DatasetTheme(raw_theme)
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
    def theme(self) -> DatasetTheme:
        """The dataset's theme (palette preset + per-token overrides)."""
        return self._theme

    @property
    def primary_color(self) -> str:
        """Back-compat alias for ``theme.primary_color``.

        Older code reads ``ds.config.primary_color`` expecting a
        simple hex string. The new theme model keeps primary inside
        ``theme.overrides.primary`` (or falls back to the default
        when the admin never customised it) — this property shims
        both shapes so existing callers don't need to change.
        """
        return normalise_color(self._theme.primary_color)

    @property
    def palette(self) -> str:
        """Back-compat alias for ``theme.palette``."""
        return self._theme.palette

    @property
    def hide_unavailable_modes(self) -> bool:
        """When True, greyed-out modes are hidden from the selection grid."""
        return bool(self._settings.get('hide_unavailable_modes', False))

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
        # Strip the legacy flat `palette` / `primary_color` out of the
        # company block on serialization — the theme block is now the
        # canonical source of truth, and keeping them in both places
        # would let them drift apart on round-trips.
        clean_company = {
            k: v for k, v in self._company.items()
            if k not in ('palette', 'primary_color')
        }
        payload: dict = {
            'company': clean_company,
            'theme': self._theme.to_dict(),
            'data': {
                'csv_path': self._data.get('csv_path', ''),
                'images_dir': self._data.get('images_dir', 'static/images'),
                'scores_db_path': self._data.get('scores_db_path', f'data/{self.id}/scores.json'),
                'column_mapping': dict(self._column_mapping),
            },
        }
        if self._settings:
            payload['settings'] = dict(self._settings)
        return payload


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
