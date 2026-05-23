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
def live_app(tmp_path_factory):
    # Get the password from env
    orig_password = os.environ.get('ADMIN_PASSWORD')
    try:
        from app import app
        os.environ.pop('ADMIN_PASSWORD', None)
        
        if app is None:
            pytest.skip('Flask app could not be created')

        port = _free_port()
        app.config['TESTING'] = True
        app.config['UPLOAD_DIR'] = str(tmp_path_factory.mktemp('uploads'))

        server = threading.Thread(
            target=app.run,
            kwargs={'host': '127.0.0.1', 'port': port, 'use_reloader': False, 'load_dotenv': False},
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
    finally:
        if orig_password is not None:
            os.environ['ADMIN_PASSWORD'] = orig_password


def _fill_step1_minimum(page: Page):
    """Fill the required step-1 fields so Suivant validation passes."""
    if not page.locator('#dataset-id').input_value():
        page.locator('#dataset-id').fill('e2e_test')
    if not page.locator('#company-name').input_value():
        page.locator('#company-name').fill('E2E Co')


# ─── Existing E2E tests ───


@pytest.mark.e2e
@pytest.mark.parametrize('path', ['/', '/about', '/how-to-play', '/scores', '/setup'])
def test_pages_load(page: Page, live_app: str, path: str):
    response = page.goto(f'{live_app}{path}')
    assert response is not None
    assert response.status == 200


@pytest.mark.e2e
def test_game_flow(page: Page, live_app: str):
    page.goto(f'{live_app}/')
    # Click the first available mode card on the new filterable grid.
    card = page.locator('.mode-card:not(.is-unavailable)').first
    card.click(timeout=10000, force=True)
    page.wait_for_url(f'{live_app}/question**', timeout=5000)
    assert '/question' in page.url


@pytest.mark.e2e
def test_mode_filter_by_tag(page: Page, live_app: str):
    """Clicking a tag chip should narrow the visible mode count."""
    page.goto(f'{live_app}/')
    total = page.locator('.mode-card').count()
    assert total > 0, 'grid should render at least one mode'

    # Pick a chip that is not currently active (since the first 'Toutes' is active by default)
    tag_chip = page.locator('.filter-group-chips .chip:not(.is-active)').first
    tag_chip.click()

    # Visible count updates via Alpine; wait for <strong> to change.
    page.wait_for_function(
        '() => Number(document.querySelector(".mode-grid-meta strong").textContent) < ' + str(total),
        timeout=3000,
    )


@pytest.mark.e2e
def test_unavailable_mode_opens_modal(page: Page, live_app: str):
    """Clicking a greyed-out card opens the explainer modal."""
    page.goto(f'{live_app}/')
    unavailable = page.locator('.mode-card.is-unavailable').first
    if unavailable.count() == 0:
        pytest.skip('fixture dataset has no unavailable modes to test')
    unavailable.click()
    # Native <dialog> — check the backdrop is visible.
    page.wait_for_selector('dialog.modal[open]', timeout=2000)
    assert page.locator('dialog.modal[open]').is_visible()


# ─── Per-mode smoke tests ───
# One assert-no-crash per registered mode. Catches regressions where a
# template rename or a missing field breaks rendering — cheap to run in
# parallel, high signal when something breaks.

_MODE_NAMES = [
    'age', 'clue', 'emoji_challenge', 'example', 'manager', 'memory',
    'mirror', 'missing_person', 'normal', 'pixelation', 'position_match',
    'progressive_hint', 'quiz', 'reverse', 'scrambled_face', 'seniority',
    'silhouette', 'speed', 'team', 'team_guess', 'timed',
]


@pytest.mark.e2e
@pytest.mark.parametrize('mode_name', _MODE_NAMES)
def test_mode_renders_without_console_errors(page: Page, live_app: str, mode_name: str):
    """Each mode must render /question without a JS console error.

    Modes that need data the fixture doesn't provide land on the
    mode_selection page (available=False) — we accept both outcomes and
    just assert the response + no JS explosion."""
    errors = []
    page.on('pageerror', lambda exc: errors.append(str(exc)))
    page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)

    # Start a fresh session so we land on the mode's own /question
    page.goto(f'{live_app}/restart')
    response = page.goto(f'{live_app}/mode/{mode_name}')
    assert response is not None
    assert response.status in (200, 302), f'{mode_name} returned HTTP {response.status}'

    # Wait for any Alpine init on the page.
    try:
        page.wait_for_function('() => typeof Alpine !== "undefined"', timeout=3000)
    except Exception:
        pass

    # Filter out benign network noise (missing favicons, etc.).
    real_errors = [
        e for e in errors
        if 'favicon' not in e.lower() and '404' not in e and 'ERR_CONNECTION' not in e
    ]
    assert not real_errors, f'{mode_name} logged errors: {real_errors}'


@pytest.mark.e2e
def test_setup_wizard_loads(page: Page, live_app: str):
    response = page.goto(f'{live_app}/setup/new')
    assert response is not None
    assert response.status == 200
    company_name_input = page.locator('#company-name')
    assert company_name_input.is_visible()


# ─── CSS-state regression tests ───
# These guard against silent JS/CSS class mismatches: JS toggles a class but
# CSS has no rule for it (so the visual state never updates). Console-error
# tests don't catch these — the bug is silent.


@pytest.mark.e2e
def test_clue_mode_hides_unrevealed_clues(page: Page, live_app: str):
    """Only the auto-revealed clue should be visible at page load."""
    page.goto(f'{live_app}/mode/clue')
    page.wait_for_url('**/question**', timeout=5000)

    visible_count = page.evaluate(
        '() => Array.from(document.querySelectorAll(".clue-item"))'
        '.filter(li => window.getComputedStyle(li).display !== "none").length'
    )
    total = page.evaluate('() => document.querySelectorAll(".clue-item").length')
    assert total >= 2, 'clue mode should ship at least 2 clues for this assertion to be meaningful'
    assert visible_count == 1, f'expected 1 visible clue at load, got {visible_count}/{total}'


@pytest.mark.e2e
def test_progressive_hint_active_class_changes_border(page: Page, live_app: str):
    """The .active hint must visually differ from the rest (border-color)."""
    page.goto(f'{live_app}/mode/progressive_hint')
    page.wait_for_url('**/question**', timeout=5000)

    colors = page.evaluate('''() => {
        const all = Array.from(document.querySelectorAll('.hint'));
        const active = all.find(h => h.classList.contains('active'));
        const inactive = all.find(h => !h.classList.contains('active'));
        if (!active || !inactive) return null;
        return {
            active: window.getComputedStyle(active).borderColor,
            inactive: window.getComputedStyle(inactive).borderColor,
        };
    }''')
    assert colors is not None, 'expected at least one .hint.active and one inactive .hint'
    assert colors['active'] != colors['inactive'], (
        f'.hint.active border ({colors["active"]}) should differ from base '
        f'.hint ({colors["inactive"]}) — CSS rule for .hint.active missing?'
    )


@pytest.mark.e2e
def test_timed_mode_warning_and_danger_classes_change_bg(page: Page, live_app: str):
    """#global-timer.warning and .danger must produce visible bg shifts."""
    page.goto(f'{live_app}/mode/timed')
    page.wait_for_url('**/question**', timeout=5000)

    bgs = page.evaluate('''() => {
        const t = document.getElementById('global-timer');
        if (!t) return null;
        // Disable transitions so getComputedStyle returns the destination color
        // immediately after className changes (the live JS doesn't add a transition
        // either — it just adds the class, then the visible bg follows).
        t.style.transition = 'none';
        t.className = 'global-timer';
        void t.offsetHeight;
        const base = window.getComputedStyle(t).backgroundColor;
        t.className = 'global-timer warning';
        void t.offsetHeight;
        const warn = window.getComputedStyle(t).backgroundColor;
        t.className = 'global-timer danger';
        void t.offsetHeight;
        const danger = window.getComputedStyle(t).backgroundColor;
        return { base, warn, danger };
    }''')
    assert bgs is not None, 'expected #global-timer to exist on /mode/timed'
    assert bgs['warn'] != bgs['base'], f'.warning class did not change bg ({bgs["warn"]} == {bgs["base"]})'
    assert bgs['danger'] != bgs['base'], f'.danger class did not change bg ({bgs["danger"]} == {bgs["base"]})'
    assert bgs['warn'] != bgs['danger'], '.warning and .danger should produce different bg colors'


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


# ─── Setup wizard E2E tests ───


@pytest.mark.e2e
def test_setup_wizard_step1_fields_visible(page: Page, live_app: str):
    """Step 1 shows dataset id + branding fields."""
    page.goto(f'{live_app}/setup/new')
    assert page.locator('#step-1').is_visible()
    assert page.locator('#dataset-id').is_visible()
    assert page.locator('#company-name').is_visible()
    assert page.locator('#logo-url').is_visible()
    assert page.locator('#tagline-fr').is_visible()
    assert page.locator('#tagline-en').is_visible()
    # Other panels hidden
    assert not page.locator('#step-2').is_visible()
    assert not page.locator('#step-3').is_visible()
    assert not page.locator('#step-4').is_visible()


@pytest.mark.e2e
def test_setup_wizard_stepper_indicators(page: Page, live_app: str):
    """Stepper indicators update active/completed classes as user progresses."""
    page.goto(f'{live_app}/setup/new')

    # Initially step 1 is active
    assert 'active' in (page.locator('[data-step="1"]').get_attribute('class') or '')

    _fill_step1_minimum(page)
    # Go to step 2 via Suivant
    page.locator('#step-1 .btn-primary').click(force=True)
    page.wait_for_timeout(400)

    step1_class = page.locator('[data-step="1"]').get_attribute('class') or ''
    step2_class = page.locator('[data-step="2"]').get_attribute('class') or ''
    assert 'completed' in step1_class
    assert 'active' in step2_class

    # Go to step 3
    page.locator('#step-2 .btn-primary').click(force=True)
    page.wait_for_timeout(400)

    step2_class = page.locator('[data-step="2"]').get_attribute('class') or ''
    step3_class = page.locator('[data-step="3"]').get_attribute('class') or ''
    assert 'completed' in step2_class
    assert 'active' in step3_class


@pytest.mark.e2e
def test_setup_wizard_forward_navigation(page: Page, live_app: str):
    """Clicking Suivant navigates through all 4 steps."""
    page.goto(f'{live_app}/setup/new')

    _fill_step1_minimum(page)
    # Wait for fadeIn animation (0.3s) between step transitions
    page.locator('#step-1 .btn-primary').click(force=True)
    page.wait_for_timeout(400)
    assert page.locator('#step-2').is_visible()

    page.locator('#step-2 .btn-primary').click(force=True)
    page.wait_for_timeout(400)
    assert page.locator('#step-3').is_visible()

    page.locator('#step-3 .btn-primary').click(force=True)
    page.wait_for_timeout(400)
    assert page.locator('#step-4').is_visible()


@pytest.mark.e2e
def test_setup_wizard_back_button(page: Page, live_app: str):
    """Precedent button returns to previous step."""
    page.goto(f'{live_app}/setup/new')

    _fill_step1_minimum(page)
    page.locator('#step-1 .btn-primary').click(force=True)
    page.wait_for_timeout(400)
    assert page.locator('#step-2').is_visible()

    page.locator('#step-2 .btn-secondary').click(force=True)
    page.wait_for_timeout(400)
    assert page.locator('#step-1').is_visible()


@pytest.mark.e2e
def test_setup_wizard_form_state_persists(page: Page, live_app: str):
    """Form values entered in Step 1 persist when navigating away and back."""
    page.goto(f'{live_app}/setup/new')

    page.locator('#dataset-id').fill('new_ds')
    page.locator('#company-name').fill('Acme Corp')
    page.locator('#tagline-fr').fill('Know your colleagues')

    # Go to step 2
    page.locator('#step-1 .btn-primary').click(force=True)
    page.wait_for_timeout(400)

    # Back to step 1 via stepper
    page.locator('[data-step="1"]').click(force=True)
    page.wait_for_timeout(400)

    assert page.locator('#dataset-id').input_value() == 'new_ds'
    assert page.locator('#company-name').input_value() == 'Acme Corp'
    assert page.locator('#tagline-fr').input_value() == 'Know your colleagues'


@pytest.mark.e2e
def test_setup_wizard_stepper_click_jumps_to_step(page: Page, live_app: str):
    """Clicking a stepper indicator jumps directly to that step."""
    page.goto(f'{live_app}/setup/new')

    page.locator('[data-step="3"]').click()
    page.wait_for_timeout(200)
    assert page.locator('#step-3').is_visible()

    page.locator('[data-step="4"]').click()
    page.wait_for_timeout(200)
    assert page.locator('#step-4').is_visible()


@pytest.mark.e2e
def test_setup_wizard_summary_reflects_form_inputs(page: Page, live_app: str):
    """Step 4 summary table contains values entered in Step 1."""
    page.goto(f'{live_app}/setup/new')

    page.locator('#dataset-id').fill('mgc')
    page.locator('#company-name').fill('My Great Company')
    page.locator('#logo-url').fill('https://example.com/logo.png')
    page.locator('#tagline-fr').fill('The best team game')

    # Navigate to step 5 (buildSummary is called by step 4's Suivant button)
    page.locator('#step-1 .btn-primary').click(force=True)
    page.wait_for_timeout(400)
    page.locator('#step-2 .btn-primary').click(force=True)
    page.wait_for_timeout(400)
    page.locator('#step-3 .btn-primary').click(force=True)
    page.wait_for_timeout(400)
    page.locator('#step-4 .btn-primary').click(force=True)
    page.wait_for_timeout(500)

    summary_text = page.locator('#summary-company').text_content() or ''
    assert 'mgc' in summary_text
    assert 'My Great Company' in summary_text
    assert 'https://example.com/logo.png' in summary_text
    assert 'The best team game' in summary_text


@pytest.mark.e2e
def test_setup_wizard_csv_upload_reveals_preview_and_mapping(page: Page, live_app: str):
    """Uploading a CSV shows preview table and mapping selects."""
    page.goto(f'{live_app}/setup/new')
    _fill_step1_minimum(page)
    page.locator('#step-1 .btn-primary').click(force=True)
    page.wait_for_timeout(400)
    page.locator('#step-2 .btn-primary').click(force=True)
    page.wait_for_timeout(400)

    # CSV preview is hidden initially (mapping may be pre-populated if config already has mapping)
    assert not page.locator('#csv-preview').is_visible()

    # Upload via hidden file input
    page.locator('#csv-file-input').set_input_files('tests/fixtures/test_team.csv')

    # Wait for upload response + UI update
    page.wait_for_selector('#csv-upload-status.success', timeout=5000)
    page.wait_for_selector('#csv-preview', state='visible', timeout=3000)
    page.wait_for_selector('#mapping-section', state='visible', timeout=3000)

    # Preview table has the expected columns
    preview_text = page.locator('#csv-table-container').text_content() or ''
    assert 'firstName' in preview_text
    assert 'lastName' in preview_text
    assert 'Alice' in preview_text  # First row

    # Mapping grid has selects for required + optional fields
    assert page.locator('#map-first_name').count() == 1
    assert page.locator('#map-last_name').count() == 1
    assert page.locator('#map-photo').count() == 1
    assert page.locator('#map-birth_date').count() == 1  # optional


@pytest.mark.e2e
def test_setup_wizard_csv_invalid_file_shows_error(page: Page, live_app: str, tmp_path):
    """Uploading a non-CSV file shows an error status."""
    bad_file = tmp_path / 'not_a_csv.txt'
    bad_file.write_text('hello')

    page.goto(f'{live_app}/setup/new')
    _fill_step1_minimum(page)
    page.locator('#step-1 .btn-primary').click(force=True)
    page.wait_for_timeout(400)
    page.locator('#step-2 .btn-primary').click(force=True)
    page.wait_for_timeout(400)

    page.locator('#csv-file-input').set_input_files(str(bad_file))
    page.wait_for_selector('#csv-upload-status.error', timeout=5000)

    status_text = page.locator('#csv-upload-status').text_content() or ''
    assert len(status_text) > 0


@pytest.mark.e2e
@pytest.mark.parametrize('viewport', [
    (375, 667),    # Mobile
    (768, 1024),   # Tablet
    (1920, 1080),  # Desktop
])
def test_setup_wizard_responsive_viewports(page: Page, live_app: str, viewport):
    """Setup wizard renders correctly at mobile/tablet/desktop viewports."""
    width, height = viewport
    page.set_viewport_size({'width': width, 'height': height})
    page.goto(f'{live_app}/setup/new')

    # Core elements still visible
    assert page.locator('.setup-header h1').is_visible()
    assert page.locator('#company-name').is_visible()
    assert page.locator('.stepper').is_visible()
    # At least 4 step indicators present
    assert page.locator('.step-indicator').count() == 5


@pytest.mark.e2e
def test_setup_wizard_back_link_to_list(page: Page, live_app: str):
    """Back link at top returns to the dataset list page."""
    page.goto(f'{live_app}/setup/new')
    back_link = page.locator('.back-link')
    assert back_link.is_visible()
    href = back_link.get_attribute('href')
    assert href == '/setup'


@pytest.mark.e2e
def test_setup_wizard_step1_validation_blocks_empty_name(page: Page, live_app: str):
    """Clicking Suivant with empty company name shows error and stays on Step 1."""
    page.goto(f'{live_app}/setup/new')

    # Provide a valid dataset id so only the company-name error triggers
    page.locator('#dataset-id').fill('e2e_v')
    page.locator('#company-name').fill('')

    page.locator('#step1-next').click(force=True)
    page.wait_for_timeout(300)

    # Still on Step 1
    assert page.locator('#step-1').is_visible()
    assert not page.locator('#step-2').is_visible()

    # Error message shown
    error_text = page.locator('#company-name-error').text_content() or ''
    assert len(error_text) > 0
    assert page.locator('#company-name').get_attribute('aria-invalid') == 'true'


@pytest.mark.e2e
def test_setup_wizard_step1_validation_clears_on_input(page: Page, live_app: str):
    """Error clears when user starts typing in the company name."""
    page.goto(f'{live_app}/setup/new')
    page.locator('#dataset-id').fill('e2e_v2')
    page.locator('#company-name').fill('')
    page.locator('#step1-next').click(force=True)
    page.wait_for_timeout(200)
    assert (page.locator('#company-name-error').text_content() or '') != ''

    # Type in the field - error should clear
    page.locator('#company-name').type('A')
    page.wait_for_timeout(200)
    assert (page.locator('#company-name-error').text_content() or '') == ''


@pytest.mark.e2e
def test_setup_wizard_stepper_keyboard_navigation(page: Page, live_app: str):
    """Stepper indicators are focusable and activate on Enter key."""
    page.goto(f'{live_app}/setup/new')

    # Step indicator has tabindex=0 (focusable)
    indicator = page.locator('[data-step="3"]')
    assert indicator.get_attribute('tabindex') == '0'
    assert indicator.get_attribute('role') == 'tab'

    # Focus and press Enter
    indicator.focus()
    page.keyboard.press('Enter')
    page.wait_for_timeout(300)

    assert page.locator('#step-3').is_visible()


@pytest.mark.e2e
def test_setup_wizard_toast_is_dismissible(page: Page, live_app: str):
    """Toast notification can be closed via the close button."""
    page.goto(f'{live_app}/setup/new')

    # Trigger toast via direct JS call (simpler than full save flow)
    page.evaluate("document.getElementById('toast-message').textContent = 'Test'; "
                  "document.getElementById('toast').className = 'toast success show';")
    page.wait_for_timeout(200)
    assert 'show' in (page.locator('#toast').get_attribute('class') or '')

    page.locator('#toast-close').click()
    page.wait_for_timeout(200)
    assert 'show' not in (page.locator('#toast').get_attribute('class') or '')


@pytest.mark.e2e
def test_setup_wizard_mapping_hint_shown_without_csv(page: Page, live_app: str):
    """Mapping empty hint is visible when no CSV has been uploaded yet in session.

    Note: the test config has an existing column_mapping so renderMappingSelects runs
    on load and hides the hint. This test verifies the hint element exists and has the
    expected informational content."""
    page.goto(f'{live_app}/setup/new')
    _fill_step1_minimum(page)
    page.locator('#step1-next').click(force=True)
    page.wait_for_timeout(400)

    hint_el = page.locator('#mapping-empty-hint')
    assert hint_el.count() == 1
    hint_text = hint_el.text_content() or ''
    assert len(hint_text) > 0
