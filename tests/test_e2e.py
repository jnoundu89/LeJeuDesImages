import os
import socket
import threading
import time

import pytest
from playwright.sync_api import Page

os.environ.setdefault('APP_CONFIG', 'tests/fixtures/e2e_config.yaml')


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='module')
def live_app():
    from app import app
    if app is None:
        pytest.skip('Flask app could not be created')

    port = _free_port()
    app.config['TESTING'] = True

    server = threading.Thread(
        target=app.run,
        kwargs={'host': '127.0.0.1', 'port': port, 'use_reloader': False},
        daemon=True,
    )
    server.start()

    for _ in range(50):
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.1)

    yield f'http://127.0.0.1:{port}'


# ─── Existing E2E tests ───


@pytest.mark.e2e
@pytest.mark.parametrize('path', ['/', '/about', '/how-to-play', '/scores'])
def test_pages_load(page: Page, live_app: str, path: str):
    response = page.goto(f'{live_app}{path}')
    assert response is not None
    assert response.status == 200


@pytest.mark.e2e
def test_game_flow(page: Page, live_app: str):
    page.goto(f'{live_app}/')
    play_button = page.locator('a.mode-button').first
    play_button.click(timeout=10000, force=True)
    page.wait_for_url(f'{live_app}/question**', timeout=5000)
    assert '/question' in page.url


@pytest.mark.e2e
@pytest.mark.skip(reason='setup.html has a pre-existing Jinja2 escape bug')
def test_setup_wizard_loads(page: Page, live_app: str):
    page.goto(f'{live_app}/setup')
    company_name_input = page.locator('#company-name')
    assert company_name_input.is_visible()


# ─── Alpine.js integration tests ───


@pytest.mark.e2e
def test_alpine_timer_counts_down(page: Page, live_app: str):
    """Timer should decrement from 60 using Alpine.js."""
    page.goto(f'{live_app}/mode/pixelation')
    page.wait_for_url('**/question**', timeout=5000)

    # Wait for Alpine to init
    page.wait_for_function('() => typeof Alpine !== "undefined" && Alpine.store("game")', timeout=5000)

    # Read initial timer
    initial = page.evaluate('() => document.getElementById("timer").textContent')
    assert 'restant' in initial.lower() or 'remaining' in initial.lower()

    # Wait 2s and check it decreased
    page.wait_for_timeout(2000)
    after = page.evaluate('() => document.getElementById("timer").textContent')
    assert initial != after, 'Timer should have changed after 2 seconds'


@pytest.mark.e2e
def test_alpine_score_updates_on_answer(page: Page, live_app: str):
    """Score should update reactively after clicking an answer."""
    page.goto(f'{live_app}/mode/pixelation')
    page.wait_for_url('**/question**', timeout=5000)
    page.wait_for_function('() => typeof Alpine !== "undefined" && Alpine.store("game")', timeout=5000)

    # Score should be 0 initially
    score_before = page.evaluate('() => Alpine.store("game").score')
    assert score_before == 0

    # Click first choice button
    page.locator('#name-choices button').first.click()
    page.wait_for_timeout(500)

    # answersCount should be 1 now
    answers = page.evaluate('() => Alpine.store("game").answersCount')
    assert answers == 1


@pytest.mark.e2e
def test_alpine_next_button_enables_after_answer(page: Page, live_app: str):
    """Next button should be disabled initially, enabled after answer."""
    page.goto(f'{live_app}/mode/pixelation')
    page.wait_for_url('**/question**', timeout=5000)
    page.wait_for_function('() => typeof Alpine !== "undefined" && Alpine.store("game")', timeout=5000)

    # Initially disabled
    is_disabled = page.evaluate('() => document.getElementById("next").disabled')
    assert is_disabled is True

    # Click an answer
    page.locator('#name-choices button').first.click()
    page.wait_for_timeout(500)

    # Now enabled
    is_disabled = page.evaluate('() => document.getElementById("next").disabled')
    assert is_disabled is False


@pytest.mark.e2e
def test_alpine_normal_mode_4_steps(page: Page, live_app: str):
    """Normal mode should reveal 4 steps sequentially with Alpine."""
    page.goto(f'{live_app}/mode/normal')
    page.wait_for_url('**/question**', timeout=5000)
    page.wait_for_function('() => typeof Alpine !== "undefined" && Alpine.store("game")', timeout=5000)

    # Click through 4 steps using JS (Alpine x-show may hide elements from Playwright)
    page.evaluate('''() => {
        return new Promise(resolve => {
            function clickNext(step) {
                if (step >= 4) { resolve(); return; }
                const sections = document.querySelectorAll('.game-section > div');
                if (sections[step]) {
                    const btn = sections[step].querySelector('button:not(:disabled)');
                    if (btn) btn.click();
                }
                setTimeout(() => clickNext(step + 1), 1000);
            }
            clickNext(0);
        });
    }''')
    page.wait_for_timeout(500)

    # All 4 answered
    answers = page.evaluate('() => Alpine.store("game").answersCount')
    assert answers == 4

    # Next button enabled
    is_disabled = page.evaluate('() => document.getElementById("next").disabled')
    assert is_disabled is False


@pytest.mark.e2e
def test_alpine_reverse_mode_image_click(page: Page, live_app: str):
    """Reverse mode: clicking an image should enable next button."""
    page.goto(f'{live_app}/mode/reverse')
    page.wait_for_url('**/question**', timeout=5000)
    page.wait_for_function('() => typeof Alpine !== "undefined" && Alpine.store("game")', timeout=5000)

    # Click first image
    page.locator('#image-choices .choice-btn').first.click()
    page.wait_for_timeout(500)

    # Next enabled
    is_disabled = page.evaluate('() => document.getElementById("next").disabled')
    assert is_disabled is False


@pytest.mark.e2e
def test_alpine_progress_bar_shows_correctly(page: Page, live_app: str):
    """Progress bar should show current/total questions."""
    page.goto(f'{live_app}/mode/pixelation')
    page.wait_for_url('**/question**', timeout=5000)
    page.wait_for_function('() => typeof Alpine !== "undefined"', timeout=5000)

    progress_text = page.locator('.progress-bar-fill').text_content()
    assert progress_text is not None
    assert '/' in progress_text  # e.g. "1/10"


@pytest.mark.e2e
def test_full_game_submit_and_next(page: Page, live_app: str):
    """Click answer, click next, verify new question loads."""
    page.goto(f'{live_app}/mode/pixelation')
    page.wait_for_url('**/question**', timeout=5000)
    page.wait_for_function('() => typeof Alpine !== "undefined" && Alpine.store("game")', timeout=5000)

    # Answer
    page.locator('#name-choices button').first.click()
    page.wait_for_timeout(500)

    # Click next (submit form)
    page.locator('#next').click()
    page.wait_for_url('**/question**', timeout=5000)

    # New question loaded (timer reset, answers reset)
    page.wait_for_function('() => typeof Alpine !== "undefined" && Alpine.store("game")', timeout=5000)
    answers = page.evaluate('() => Alpine.store("game").answersCount')
    assert answers == 0  # Reset for new question


@pytest.mark.e2e
@pytest.mark.parametrize('mode', ['age', 'seniority', 'quiz', 'team_guess', 'clue', 'mirror'])
def test_mode_loads_with_alpine(page: Page, live_app: str, mode: str):
    """Each mode should load with Alpine store initialized."""
    page.goto(f'{live_app}/mode/{mode}')
    page.wait_for_url('**/question**', timeout=5000)
    page.wait_for_function('() => typeof Alpine !== "undefined" && Alpine.store("game")', timeout=5000)

    store = page.evaluate('() => ({ score: Alpine.store("game").score, maxScore: Alpine.store("game").maxScore })')
    assert store['maxScore'] > 0
    assert store['score'] == 0
