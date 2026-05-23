"""Integration tests for game routes: /mode, /question, /check, /result."""
import pytest

TESTABLE_MODES = [
    'normal', 'reverse', 'pixelation', 'timed', 'speed', 'mirror',
    'silhouette', 'scrambled_face', 'emoji_challenge', 'clue',
    'team_guess', 'example', 'progressive_hint', 'missing_person',
    'manager', 'seniority', 'age', 'quiz', 'team', 'position_match',
    'memory',
]


class TestModeInit:
    """Test /mode/<name> initializes the session correctly."""

    @pytest.mark.parametrize('mode_name', TESTABLE_MODES)
    def test_mode_init_redirects_to_question(self, client, mode_name):
        resp = client.get(f'/mode/{mode_name}')
        assert resp.status_code == 302
        assert '/question' in resp.headers['Location']

    def test_invalid_mode_redirects_to_index(self, client):
        resp = client.get('/mode/nonexistent')
        assert resp.status_code == 302


class TestQuestionPage:
    """Test /question renders correctly for each mode."""

    @pytest.mark.parametrize('mode_name', TESTABLE_MODES)
    def test_question_page_returns_200(self, client, mode_name):
        # Init the mode first
        client.get(f'/mode/{mode_name}')
        resp = client.get('/question')
        assert resp.status_code == 200

    @pytest.mark.parametrize('mode_name', TESTABLE_MODES)
    def test_question_page_no_server_error(self, client, mode_name):
        client.get(f'/mode/{mode_name}')
        resp = client.get('/question')
        assert b'Traceback' not in resp.data
        assert b'KeyError' not in resp.data
        assert b'TypeError' not in resp.data


class TestCheckEndpoint:
    """Test POST /check processes answers."""

    def test_check_with_correct_answer(self, client):
        client.get('/mode/pixelation')
        resp = client.post('/check', data={
            'correct_answer': '1',
            'score_increment': '1',
        })
        # Should redirect to /question or /result
        assert resp.status_code == 302

    def test_check_with_wrong_answer(self, client):
        client.get('/mode/pixelation')
        resp = client.post('/check', data={
            'correct_answer': '0',
            'score_increment': '0',
        })
        assert resp.status_code == 302

    def test_check_without_session_redirects(self, client):
        # Clear session by visiting a fresh client
        with client.session_transaction() as sess:
            sess.clear()
        resp = client.post('/check', data={'correct_answer': '0'})
        # Should handle gracefully (redirect to index)
        assert resp.status_code in (302, 200)


class TestResultPage:
    """Test /result page."""

    def test_result_page_loads(self, client):
        # Init and play through a quick mode
        client.get('/mode/pixelation')
        resp = client.get('/result')
        # Should render or redirect
        assert resp.status_code in (200, 302)


class TestStaticPages:
    """Test non-game pages."""

    def test_homepage_loads(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_about_loads(self, client):
        resp = client.get('/about')
        assert resp.status_code == 200

    def test_scores_loads(self, client):
        resp = client.get('/scores')
        assert resp.status_code == 200

    def test_how_to_play_loads(self, client):
        resp = client.get('/how-to-play')
        assert resp.status_code == 200

    def test_restart_redirects(self, client):
        resp = client.get('/restart')
        assert resp.status_code == 302
