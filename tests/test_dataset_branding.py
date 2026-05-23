"""Tests for dataset branding extensions (primary_color, hide_unavailable_modes)."""
import pytest

from models.config import DEFAULT_PRIMARY_COLOR, DatasetConfig


def _minimal_mapping():
    return {
        'first_name': 'fn', 'last_name': 'ln', 'photo': 'p', 'team': 't',
        'job_title': 'jt', 'company': 'c', 'sex': 's',
    }


def _make(raw: dict) -> DatasetConfig:
    raw.setdefault('data', {'csv_path': 'x.csv', 'column_mapping': _minimal_mapping()})
    return DatasetConfig('acme', raw)


class TestPrimaryColor:
    def test_default_when_unset(self):
        ds = _make({'company': {'name': 'Acme'}})
        assert ds.primary_color == DEFAULT_PRIMARY_COLOR

    def test_valid_hex_kept(self):
        ds = _make({'company': {'primary_color': '#FF5733'}})
        assert ds.primary_color == '#FF5733'

    def test_invalid_hex_falls_back_to_default(self):
        ds = _make({'company': {'primary_color': 'not-a-color'}})
        assert ds.primary_color == DEFAULT_PRIMARY_COLOR

    def test_short_hex_rejected(self):
        # We only accept full 6-digit hex to avoid ambiguity.
        ds = _make({'company': {'primary_color': '#abc'}})
        assert ds.primary_color == DEFAULT_PRIMARY_COLOR

    def test_missing_hash_rejected(self):
        ds = _make({'company': {'primary_color': 'FF5733'}})
        assert ds.primary_color == DEFAULT_PRIMARY_COLOR


class TestHideUnavailableModes:
    def test_default_is_false(self):
        ds = _make({'company': {'name': 'Acme'}})
        assert ds.hide_unavailable_modes is False

    def test_explicit_true(self):
        ds = _make({
            'company': {'name': 'Acme'},
            'settings': {'hide_unavailable_modes': True},
        })
        assert ds.hide_unavailable_modes is True

    def test_explicit_false(self):
        ds = _make({
            'company': {'name': 'Acme'},
            'settings': {'hide_unavailable_modes': False},
        })
        assert ds.hide_unavailable_modes is False


class TestToDictPreservesSettings:
    def test_settings_omitted_when_empty(self):
        ds = _make({'company': {'name': 'Acme'}})
        assert 'settings' not in ds.to_dict()

    def test_settings_included_when_present(self):
        ds = _make({
            'company': {'name': 'Acme', 'primary_color': '#FF0000'},
            'settings': {'hide_unavailable_modes': True},
        })
        d = ds.to_dict()
        assert d['settings'] == {'hide_unavailable_modes': True}
        # Legacy `company.primary_color` is migrated into the new
        # nested theme block so the disk format stays canonical.
        assert 'primary_color' not in d['company']
        assert d['theme']['overrides']['primary'] == '#FF0000'


class TestPalette:
    def test_default_is_corporate(self):
        ds = _make({'company': {'name': 'Acme'}})
        assert ds.palette == 'corporate'

    def test_all_known_palettes_preserved(self):
        from models.config import PALETTE_KEYS
        # 16 standard (9 light + 7 dark) + 1 special (legacy) = 17 total.
        assert len(PALETTE_KEYS) == 17, 'expected 17 palette presets'
        for key in PALETTE_KEYS:
            ds = _make({'company': {'palette': key}})
            assert ds.palette == key, f'{key} not preserved'

    def test_palette_groups_partition_keys(self):
        from models.config import (
            DARK_PALETTE_KEYS,
            LIGHT_PALETTE_KEYS,
            PALETTE_KEYS,
            SPECIAL_PALETTE_KEYS,
        )
        # special and light are disjoint; legacy lives in dark + special.
        assert LIGHT_PALETTE_KEYS.isdisjoint(SPECIAL_PALETTE_KEYS)
        assert LIGHT_PALETTE_KEYS.isdisjoint(DARK_PALETTE_KEYS)
        assert SPECIAL_PALETTE_KEYS.issubset(DARK_PALETTE_KEYS)
        assert LIGHT_PALETTE_KEYS | DARK_PALETTE_KEYS == set(PALETTE_KEYS)

    def test_legacy_palette_accepted(self):
        ds = _make({'company': {'palette': 'legacy'}})
        assert ds.palette == 'legacy'

    def test_unknown_palette_falls_back_to_default(self):
        ds = _make({'company': {'palette': 'neon_purple'}})
        assert ds.palette == 'corporate'

    def test_palette_and_primary_are_independent(self):
        """warm palette + custom primary color should both round-trip."""
        ds = _make({
            'company': {'palette': 'warm', 'primary_color': '#FF5733'},
        })
        assert ds.palette == 'warm'
        assert ds.primary_color == '#FF5733'

    def test_midnight_palette_accepted(self):
        """The 'midnight' palette is the user-preferred dark-but-not-black."""
        ds = _make({'company': {'palette': 'midnight'}})
        assert ds.palette == 'midnight'


class TestDatasetTheme:
    def test_default_theme_has_corporate_palette_no_overrides(self):
        ds = _make({'company': {'name': 'Acme'}})
        assert ds.theme.palette == 'corporate'
        assert ds.theme.overrides == {}
        assert ds.theme.primary_color == '#4F46E5'

    def test_new_theme_block_is_read(self):
        ds = _make({
            'theme': {
                'palette': 'midnight',
                'overrides': {
                    'surface': '#3E4A7A',
                    'text-soft': '#C8D0F0',
                },
            },
        })
        assert ds.theme.palette == 'midnight'
        assert ds.theme.overrides == {
            'surface': '#3E4A7A',
            'text-soft': '#C8D0F0',
        }

    def test_unknown_override_keys_are_dropped(self):
        """Only the 7 editable tokens survive — garbage is filtered."""
        ds = _make({
            'theme': {
                'palette': 'ocean',
                'overrides': {
                    'surface': '#1F548F',
                    'unknown_token': '#000000',   # should be dropped
                    '__proto__': '#FF0000',       # should be dropped
                },
            },
        })
        assert ds.theme.overrides == {'surface': '#1F548F'}

    def test_invalid_hex_values_are_dropped(self):
        ds = _make({
            'theme': {
                'palette': 'ocean',
                'overrides': {
                    'surface': '#1F548F',
                    'text': 'not-a-color',        # dropped
                    'border': '#abc',             # dropped (short form)
                    'primary': 'FF5733',          # dropped (missing #)
                },
            },
        })
        assert ds.theme.overrides == {'surface': '#1F548F'}

    def test_unknown_palette_falls_back_to_default(self):
        ds = _make({'theme': {'palette': 'rainbow_unicorn'}})
        assert ds.theme.palette == 'corporate'

    def test_primary_override_exposed_as_primary_color(self):
        """Back-compat: ds.config.primary_color returns the override."""
        ds = _make({
            'theme': {
                'palette': 'midnight',
                'overrides': {'primary': '#FF4D4D'},
            },
        })
        assert ds.primary_color == '#FF4D4D'
        assert ds.theme.primary_color == '#FF4D4D'

    def test_legacy_flat_palette_and_primary_migrated(self):
        """Pre-refactor configs with flat company.palette + company.primary_color
        are read seamlessly — no manual migration needed."""
        ds = _make({
            'company': {
                'name': 'Legacy',
                'palette': 'warm',
                'primary_color': '#FF8800',
            },
        })
        assert ds.theme.palette == 'warm'
        assert ds.theme.overrides == {'primary': '#FF8800'}
        assert ds.primary_color == '#FF8800'
        # Round-trip emits the new canonical shape
        d = ds.to_dict()
        assert d['theme']['palette'] == 'warm'
        assert d['theme']['overrides']['primary'] == '#FF8800'
        # And DOESN'T keep the legacy keys on company
        assert 'palette' not in d['company']
        assert 'primary_color' not in d['company']

    def test_legacy_default_primary_not_persisted_as_override(self):
        """Reading a legacy config where primary_color happens to equal the
        default should NOT create a noisy '# same-as-default' override."""
        ds = _make({
            'company': {
                'name': 'Legacy',
                'palette': 'warm',
                'primary_color': '#4F46E5',  # == DEFAULT_PRIMARY_COLOR
            },
        })
        assert ds.theme.overrides == {}

    def test_resolved_overrides_returns_just_the_overrides(self):
        ds = _make({
            'theme': {
                'palette': 'midnight',
                'overrides': {'surface': '#3E4A7A'},
            },
        })
        assert ds.theme.resolved_overrides() == {'surface': '#3E4A7A'}

    def test_to_dict_omits_empty_overrides(self):
        ds = _make({'theme': {'palette': 'forest'}})
        d = ds.to_dict()
        assert d['theme'] == {'palette': 'forest'}  # no 'overrides' key


class TestBackgroundEffect:
    def test_default_is_nasa_for_regular_palettes(self):
        # NASA is the new default (matches the user's reference at
        # vincentgarreau.com/particles.js/#nasa).
        ds = _make({'theme': {'palette': 'midnight'}})
        assert ds.theme.background_effect == 'nasa'
        assert ds.theme.background_effect_explicit is None

    def test_legacy_palette_defaults_to_fireworks(self):
        # Back-compat: a legacy dataset without an explicit field
        # keeps auto-fireworks.
        ds = _make({'theme': {'palette': 'legacy'}})
        assert ds.theme.background_effect == 'fireworks'
        assert ds.theme.background_effect_explicit is None

    def test_explicit_fireworks_on_non_legacy_palette(self):
        ds = _make({'theme': {'palette': 'midnight', 'background_effect': 'fireworks'}})
        assert ds.theme.background_effect == 'fireworks'
        assert ds.theme.background_effect_explicit == 'fireworks'

    def test_explicit_nasa_on_legacy_overrides_default(self):
        # Admin can opt out of fireworks even when on legacy.
        ds = _make({'theme': {'palette': 'legacy', 'background_effect': 'nasa'}})
        assert ds.theme.background_effect == 'nasa'
        assert ds.theme.background_effect_explicit == 'nasa'

    def test_unknown_value_falls_back_to_default(self):
        ds = _make({'theme': {'palette': 'midnight', 'background_effect': 'lasers'}})
        assert ds.theme.background_effect == 'nasa'
        assert ds.theme.background_effect_explicit is None

    def test_legacy_particles_value_aliases_to_nasa(self):
        # Configs from the previous schema stored 'particles' as the
        # constellation effect. The alias rewrites that to 'nasa'.
        ds = _make({'theme': {'palette': 'midnight', 'background_effect': 'particles'}})
        assert ds.theme.background_effect == 'nasa'
        # The alias resolves at load time, so the explicit field
        # already reflects the new key — no orphaned 'particles' on
        # disk after a save round-trip.
        assert ds.theme.background_effect_explicit == 'nasa'

    def test_all_named_presets_round_trip(self):
        for preset in ('nasa', 'default', 'snow', 'bubble', 'star', 'fireworks', 'none'):
            ds = _make({'theme': {'palette': 'midnight', 'background_effect': preset}})
            assert ds.theme.background_effect == preset

    def test_to_dict_persists_explicit_value(self):
        ds = _make({'theme': {'palette': 'midnight', 'background_effect': 'fireworks'}})
        assert ds.to_dict()['theme']['background_effect'] == 'fireworks'

    def test_to_dict_omits_implicit_value(self):
        # Legacy default fireworks should NOT show up on disk.
        ds = _make({'theme': {'palette': 'legacy'}})
        d = ds.to_dict()
        assert 'background_effect' not in d['theme']


class TestCardEffect:
    """`theme.card_effect` controls the gold shine sweep on `.mode-card`
    hover. Defaults to 'shine' for the legacy palette (back-compat
    with the original legacy-only effect), 'none' otherwise."""

    def test_default_is_none_for_regular_palette(self):
        ds = _make({'theme': {'palette': 'midnight'}})
        assert ds.theme.card_effect == 'none'
        assert ds.theme.card_effect_explicit is None

    def test_default_is_shine_for_legacy_palette(self):
        ds = _make({'theme': {'palette': 'legacy'}})
        assert ds.theme.card_effect == 'shine'
        assert ds.theme.card_effect_explicit is None

    def test_explicit_shine_on_non_legacy_palette(self):
        ds = _make({'theme': {'palette': 'slate', 'card_effect': 'shine'}})
        assert ds.theme.card_effect == 'shine'
        assert ds.theme.card_effect_explicit == 'shine'

    def test_explicit_none_overrides_legacy_default(self):
        ds = _make({'theme': {'palette': 'legacy', 'card_effect': 'none'}})
        assert ds.theme.card_effect == 'none'

    def test_unknown_value_falls_back_to_palette_default(self):
        ds = _make({'theme': {'palette': 'midnight', 'card_effect': 'wobble'}})
        assert ds.theme.card_effect == 'none'
        assert ds.theme.card_effect_explicit is None

    def test_to_dict_persists_explicit_value(self):
        ds = _make({'theme': {'palette': 'midnight', 'card_effect': 'shine'}})
        assert ds.to_dict()['theme']['card_effect'] == 'shine'

    def test_to_dict_omits_implicit_value(self):
        ds = _make({'theme': {'palette': 'legacy'}})
        assert 'card_effect' not in ds.to_dict()['theme']


class TestComponentTokens:
    """`card-bg`, `card-text`, `footer-bg`, `footer-text` are editable
    on top of the base surface/text tokens. Each falls back to the
    matching base token at the CSS layer, so a dataset that doesn't
    customise them keeps the previous look."""

    @pytest.mark.parametrize('token, value', [
        ('card-bg', '#1F2A4D'),
        ('card-text', '#EDF2FF'),
        ('footer-bg', '#000000'),
        ('footer-text', '#888888'),
    ])
    def test_each_token_round_trips(self, token, value):
        ds = _make({'theme': {'palette': 'slate', 'overrides': {token: value}}})
        assert ds.theme.overrides == {token: value}
        # Round-trip via to_dict() preserves the override.
        assert ds.to_dict()['theme']['overrides'][token] == value

    def test_invalid_hex_dropped(self):
        ds = _make({'theme': {'palette': 'slate', 'overrides': {
            'card-bg': 'not-a-hex',
            'footer-text': '#FF0000',
        }}})
        # Invalid value silently dropped; valid one survives.
        assert ds.theme.overrides == {'footer-text': '#FF0000'}

    def test_resolved_overrides_includes_components(self):
        # The inline-style emitter relies on resolved_overrides() so the
        # 4 new tokens must come out in the dict.
        ds = _make({'theme': {'palette': 'slate', 'overrides': {
            'card-bg': '#111111',
            'card-text': '#FFFFFF',
            'footer-bg': '#222222',
            'footer-text': '#CCCCCC',
        }}})
        resolved = ds.theme.resolved_overrides()
        assert resolved['card-bg'] == '#111111'
        assert resolved['card-text'] == '#FFFFFF'
        assert resolved['footer-bg'] == '#222222'
        assert resolved['footer-text'] == '#CCCCCC'


class TestThemePresets:
    """`theme.presets` lets a dataset stash named alternative themes.
    The wizard can apply / delete them; the apply route swaps the
    active theme to the preset's values without touching the rest of
    the dataset config."""

    def test_no_presets_by_default(self):
        ds = _make({'theme': {'palette': 'midnight'}})
        assert ds.theme.presets == {}

    def test_presets_round_trip(self):
        ds = _make({'theme': {
            'palette': 'slate',
            'overrides': {'primary': '#FF0000'},
            'presets': {
                'Light': {
                    'palette': 'slate',
                    'overrides': {'primary': '#3A61F7', 'bg': '#F8F9FB'},
                },
                'Dark': {
                    'palette': 'slate',
                    'overrides': {'primary': '#1ADC77', 'bg': '#041E42'},
                    'background_effect': 'fireworks',
                },
            },
        }})
        presets = ds.theme.presets
        assert set(presets.keys()) == {'Light', 'Dark'}
        assert presets['Light']['overrides'] == {'primary': '#3A61F7', 'bg': '#F8F9FB'}
        assert presets['Dark']['overrides'] == {'primary': '#1ADC77', 'bg': '#041E42'}
        assert presets['Dark']['background_effect'] == 'fireworks'

    def test_presets_drop_invalid_entries(self):
        ds = _make({'theme': {
            'palette': 'slate',
            'presets': {
                # Empty key — dropped.
                '': {'palette': 'midnight'},
                # Non-dict value — dropped.
                'Bad': 'just a string',
                # Valid one survives.
                'Good': {'palette': 'midnight', 'overrides': {'primary': '#1ADC77'}},
            },
        }})
        assert list(ds.theme.presets.keys()) == ['Good']

    def test_presets_normalise_inner_overrides(self):
        # Garbage hex values + unknown keys are dropped from the inner
        # overrides exactly like the top-level overrides.
        ds = _make({'theme': {
            'palette': 'slate',
            'presets': {
                'Mix': {
                    'palette': 'slate',
                    'overrides': {
                        'primary': '#1ADC77',
                        'evil_key': '#FF0000',
                        'bg': 'not-a-hex',
                    },
                },
            },
        }})
        assert ds.theme.presets['Mix']['overrides'] == {'primary': '#1ADC77'}

    def test_presets_caller_cant_mutate_internal_state(self):
        ds = _make({'theme': {
            'palette': 'slate',
            'presets': {'X': {'palette': 'slate', 'overrides': {'primary': '#1ADC77'}}},
        }})
        snapshot = ds.theme.presets
        snapshot['X']['overrides']['primary'] = '#000000'
        # Re-read returns the original value.
        assert ds.theme.presets['X']['overrides']['primary'] == '#1ADC77'

    def test_to_dict_omits_empty_presets(self):
        ds = _make({'theme': {'palette': 'slate'}})
        d = ds.to_dict()
        assert 'presets' not in d['theme']

    def test_to_dict_persists_presets(self):
        ds = _make({'theme': {
            'palette': 'slate',
            'presets': {'Light': {'palette': 'slate', 'overrides': {'primary': '#3A61F7'}}},
        }})
        d = ds.to_dict()
        assert 'Light' in d['theme']['presets']
        assert d['theme']['presets']['Light']['overrides']['primary'] == '#3A61F7'
