import socket
import threading

import pytest
from playwright.sync_api import Page

from app import create_app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='module')
def live_app():
    port = _free_port()
    app = create_app(config_path='tests/fixtures/e2e_config.yaml')
    app.config['TESTING'] = True

    server = threading.Thread(
        target=app.run,
        kwargs={'host': '127.0.0.1', 'port': port, 'use_reloader': False},
        daemon=True,
    )
    server.start()

    # Wait for the server to be ready
    import time
    for _ in range(50):
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.1)

    yield f'http://127.0.0.1:{port}'


@pytest.mark.e2e
@pytest.mark.parametrize('path', ['/', '/about', '/how-to-play', '/scores', '/setup'])
def test_pages_load(page: Page, live_app: str, path: str):
    response = page.goto(f'{live_app}{path}')
    assert response is not None
    assert response.status == 200


@pytest.mark.e2e
def test_game_flow(page: Page, live_app: str):
    page.goto(f'{live_app}/')
    # Click the first available "play now" button
    play_button = page.locator('a.mode-button').first
    play_button.click()
    # After clicking, we should be redirected to a question page
    page.wait_for_url(f'{live_app}/question**', timeout=5000)
    assert '/question' in page.url


@pytest.mark.e2e
def test_setup_wizard_loads(page: Page, live_app: str):
    page.goto(f'{live_app}/setup')
    company_name_input = page.locator('#company-name')
    assert company_name_input.is_visible()
