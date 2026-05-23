"""Contract tests for declarative mode metadata.

Every mode must declare enough metadata for the UI to render its card
without mode-by-mode if/else. These tests guard the contract so new
modes can't land in main without filling in ``required_fields``,
``tags``, ``icon``, etc.
"""
from models.game_mode import GameMode

KNOWN_PREVIEW_TYPES = {
    'static', 'pixelation', 'silhouette', 'scrambled', 'emoji',
    'clue', 'memory', 'age', 'normal',
}


class TestModeMetadataContract:
    """Each registered mode declares the metadata the UI relies on."""

    def test_every_mode_has_required_fields(self, mode_factory):
        for mode in mode_factory.get_all_modes().values():
            assert isinstance(mode.required_fields, list), f"{mode.name}: required_fields must be a list"
            assert mode.required_fields, f"{mode.name}: required_fields must not be empty"
            assert 'photo' in mode.required_fields, f"{mode.name}: photo is always required"

    def test_every_mode_declares_valid_difficulty(self, mode_factory):
        for mode in mode_factory.get_all_modes().values():
            assert mode.difficulty in (1, 2, 3), (
                f"{mode.name}: difficulty must be 1 (easy), 2 (medium), or 3 (hard), got {mode.difficulty}"
            )

    def test_every_mode_declares_estimated_duration(self, mode_factory):
        for mode in mode_factory.get_all_modes().values():
            assert isinstance(mode.estimated_duration_sec, int)
            assert 30 <= mode.estimated_duration_sec <= 600, (
                f"{mode.name}: estimated_duration_sec {mode.estimated_duration_sec} is unrealistic"
            )

    def test_every_mode_declares_tags_list(self, mode_factory):
        for mode in mode_factory.get_all_modes().values():
            assert isinstance(mode.tags, list), f"{mode.name}: tags must be a list"

    def test_every_mode_declares_icon(self, mode_factory):
        for mode in mode_factory.get_all_modes().values():
            assert isinstance(mode.icon, str) and mode.icon, f"{mode.name}: icon must be a non-empty string"
            assert mode.icon.startswith('fa-'), f"{mode.name}: icon should be a Font Awesome class (fa-...)"

    def test_every_mode_declares_known_preview_type(self, mode_factory):
        for mode in mode_factory.get_all_modes().values():
            assert mode.preview_type in KNOWN_PREVIEW_TYPES, (
                f"{mode.name}: preview_type {mode.preview_type!r} not in {KNOWN_PREVIEW_TYPES}"
            )

    def test_score_multiplier_is_positive(self, mode_factory):
        for mode in mode_factory.get_all_modes().values():
            assert mode.score_multiplier >= 1, f"{mode.name}: score_multiplier must be >= 1"

    def test_min_eligible_is_positive(self, mode_factory):
        for mode in mode_factory.get_all_modes().values():
            assert mode.min_eligible_employees >= 1, (
                f"{mode.name}: min_eligible_employees must be >= 1"
            )


class TestMetadataDefaults:
    """Base-class defaults stay sensible so new modes inherit usable values."""

    def test_default_required_fields(self):
        assert GameMode.required_fields == ['photo', 'first_name', 'last_name']

    def test_default_min_eligible(self):
        assert GameMode.min_eligible_employees == 10

    def test_default_score_multiplier(self):
        assert GameMode.score_multiplier == 1

    def test_default_preview_type(self):
        assert GameMode.preview_type == 'static'
