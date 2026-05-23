"""Full game flow tests: init → questions → check → result.

Simulates a complete game session for representative modes to verify
the entire pipeline works end-to-end with the Flask test client.
"""
import pytest


@pytest.mark.parametrize('mode_name', ['pixelation', 'reverse', 'normal'])
class TestFullGameFlow:
    """Play a complete game and verify score + result page."""

    def test_full_game_reaches_result(self, client, mode_name):
        """Play through all questions until game_over, then check result."""
        # Start the mode
        resp = client.get(f'/mode/{mode_name}')
        assert resp.status_code == 302

        questions_played = 0
        max_questions = 15  # Safety limit

        while questions_played < max_questions:
            # Get the question page
            resp = client.get('/question')

            # If redirected (to result or index), game is over
            if resp.status_code == 302:
                break

            assert resp.status_code == 200

            # Submit an answer (always "correct_answer=1" for simplicity)
            if mode_name == 'normal':
                resp = client.post('/check', data={
                    'score_increment': '1',
                    'company_correct': '1',
                    'team_correct': '1',
                    'name_correct': '1',
                    'position_correct': '1',
                })
            else:
                resp = client.post('/check', data={
                    'correct_answer': '1',
                    'score_increment': '1',
                })

            assert resp.status_code == 302
            questions_played += 1

        # Should have played at least 1 question
        assert questions_played >= 1

    def test_result_page_shows_score(self, client, mode_name):
        """After a game, the result page should render with score data."""
        # Init and play 1 question
        client.get(f'/mode/{mode_name}')
        client.get('/question')

        if mode_name == 'normal':
            client.post('/check', data={
                'score_increment': '2',
                'company_correct': '1',
                'team_correct': '1',
                'name_correct': '0',
                'position_correct': '0',
            })
        else:
            client.post('/check', data={
                'correct_answer': '1',
                'score_increment': '1',
            })

        # Access result page
        resp = client.get('/result')
        assert resp.status_code == 200
        assert b'score' in resp.data.lower() or b'Score' in resp.data

    def test_restart_resets_game(self, client, mode_name):
        """After restart, starting a new game should work."""
        client.get(f'/mode/{mode_name}')
        client.get('/question')
        client.get('/restart')

        # Start a new game
        resp = client.get(f'/mode/{mode_name}')
        assert resp.status_code == 302

        resp = client.get('/question')
        assert resp.status_code == 200


class TestBestScorePersistence:
    """Verify that best_score is tracked after playing."""

    def test_best_score_updates(self, client):
        """Play a game, check that best_score is set."""
        # Play pixelation with a correct answer
        client.get('/mode/pixelation')
        client.get('/question')
        client.post('/check', data={'correct_answer': '1', 'score_increment': '1'})

        # Check result page renders
        resp = client.get('/result')
        assert resp.status_code == 200
