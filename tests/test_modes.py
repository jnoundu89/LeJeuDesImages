"""Contract tests for all game modes.

Each mode must satisfy the same interface: initialize(), get_question_data(),
update_score(). These parametrized tests verify this contract for all 21+ modes.
"""
import pytest

ALL_MODES = [
    'age', 'clue', 'emoji_challenge', 'example', 'manager', 'memory',
    'mirror', 'missing_person', 'pixelation', 'position_match',
    'progressive_hint', 'quiz', 'scrambled_face', 'seniority',
    'silhouette', 'speed', 'team', 'team_guess', 'timed',
    'normal', 'reverse',
]


@pytest.mark.parametrize('mode_name', ALL_MODES)
class TestModeContract:
    """Every mode must satisfy the basic GameMode contract."""

    def _get_mode(self, mode_factory, mode_name):
        mode = mode_factory.get_mode(mode_name)
        if mode is None:
            pytest.skip(f'{mode_name} not registered')
        return mode

    def test_initialize_returns_required_keys(self, mode_factory, mode_name):
        mode = self._get_mode(mode_factory, mode_name)
        result = mode.initialize()
        assert 'user_id' in result, f'{mode_name}: missing user_id'
        assert 'data_id' in result, f'{mode_name}: missing data_id'
        assert 'max_score' in result, f'{mode_name}: missing max_score'
        assert result['max_score'] > 0, f'{mode_name}: max_score should be > 0'

    def test_first_question_not_game_over(self, mode_factory, mode_name):
        mode = self._get_mode(mode_factory, mode_name)
        init = mode.initialize()
        q = mode.get_question_data(init['data_id'], [], 0)
        assert q.get('game_over') is not True, f'{mode_name}: first question is game_over'

    def test_question_returns_current_question(self, mode_factory, mode_name):
        mode = self._get_mode(mode_factory, mode_name)
        init = mode.initialize()
        q = mode.get_question_data(init['data_id'], [], 0)
        if not q.get('game_over'):
            assert 'current_question' in q, f'{mode_name}: missing current_question'

    def test_update_score_does_not_crash(self, mode_factory, mode_name):
        mode = self._get_mode(mode_factory, mode_name)
        init = mode.initialize()
        # Should not raise
        mode.update_score(init['user_id'], correct_answer=1)

    def test_question_data_no_key_error(self, mode_factory, mode_name):
        """Verify get_question_data doesn't raise KeyError on employee fields."""
        mode = self._get_mode(mode_factory, mode_name)
        init = mode.initialize()
        # Should not raise KeyError
        q = mode.get_question_data(init['data_id'], [], 0)
        assert isinstance(q, dict), f'{mode_name}: question data should be a dict'
