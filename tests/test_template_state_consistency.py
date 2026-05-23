"""Static consistency check for mode-local CSS state classes.

Catches the silent JS↔CSS mismatch pattern that doesn't raise console
errors:

  - **CSS-orphan**: a template's `{% block mode_styles %}` defines a
    compound rule like ``.foo.bar`` (a state on a parent), but no JS
    `classList.add/toggle('bar')` and no static ``class="... bar ..."``
    ever puts ``bar`` on a ``.foo`` element. The rule is dead.

  - **JS-orphan**: a template's `{% block game_scripts %}` toggles a
    class with ``classList.add('bar')`` but no CSS rule (mode-local
    *or* shared) ever styles ``.bar`` or ``.foo.bar``. The class
    name has no visual effect.

Both directions guard against the bug pattern fixed in commits
``7798e3e`` (clue), ``1cf418e`` (progressive_hint + timed). They are
purely static (no Flask, no Playwright) so they run in the fast
``make test`` suite, not ``make test-e2e``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / 'templates'
STATIC_CSS_DIRS = [ROOT / 'static', ROOT / 'static' / 'css']

# Mode templates we audit. Mirrors test_e2e._MODE_NAMES.
_MODE_TEMPLATES = [
    'age', 'clue', 'emoji_challenge', 'example', 'manager', 'memory',
    'mirror', 'missing_person', 'normal', 'pixelation', 'position_match',
    'progressive_hint', 'quiz', 'reverse', 'scrambled_face', 'seniority',
    'silhouette', 'speed', 'team', 'team_guess', 'timed',
]


def _load_shared_class_names() -> set[str]:
    """Every class defined in any static/**.css file. Used as an auto-allowlist
    so a mode's JS toggling e.g. `.correct` (defined in gameplay.css) doesn't
    look like a JS-orphan."""
    names: set[str] = set()
    for css_dir in STATIC_CSS_DIRS:
        if not css_dir.is_dir():
            continue
        for css_file in css_dir.glob('*.css'):
            text = css_file.read_text(encoding='utf-8')
            for cls in re.findall(r'\.([a-zA-Z][\w-]*)', text):
                names.add(cls)
    return names


_SHARED_CSS_CLASSES = _load_shared_class_names()


def _extract_block(template_text: str, block_name: str) -> str:
    """Return the contents of a Jinja `{% block name %}...{% endblock %}` or ''."""
    pattern = rf'\{{\%\s*block\s+{re.escape(block_name)}\s*\%\}}(.*?)\{{\%\s*endblock'
    match = re.search(pattern, template_text, re.DOTALL)
    return match.group(1) if match else ''


def _extract_compound_selectors(style_text: str) -> list[tuple[str, str]]:
    """Return [(parent, state), ...] from chained selectors like `.foo.bar`
    *or* the `:not(.bar)` form `.foo:not(.bar)`. State pseudo-classes
    (``:hover``, ``:disabled``, etc.) are intentionally not extracted."""
    chained = re.findall(r'\.([a-zA-Z][\w-]*)\.([a-zA-Z][\w-]*)(?=[\s,{:])', style_text)
    negated = re.findall(r'\.([a-zA-Z][\w-]*):not\(\.([a-zA-Z][\w-]*)\)', style_text)
    return chained + negated


def _extract_top_level_classes(style_text: str) -> set[str]:
    """Every `.foo {` (single-class) rule head, for JS-orphan checks."""
    return set(re.findall(r'\.([a-zA-Z][\w-]*)\s*[\s,{:]', style_text))


def _extract_js_toggled_classes(js_text: str) -> set[str]:
    """Args of `classList.add/toggle/remove('foo')` and `classList.add("foo")`."""
    return set(re.findall(
        r"""classList\.(?:add|toggle|remove)\s*\(\s*['"]([\w-]+)['"]""",
        js_text,
    ))


def _extract_template_html_classes(template_text: str) -> set[str]:
    """Tokens that appear inside `class="..."` attrs (including ones wrapped
    in Jinja `{% if %}` blocks). Token = bare identifier matching [a-zA-Z][\\w-]*.
    """
    classes: set[str] = set()
    for chunk in re.findall(r'class\s*=\s*["\']([^"\']*)["\']', template_text):
        for token in re.findall(r'[a-zA-Z][\w-]*', chunk):
            classes.add(token)
    return classes


@pytest.mark.parametrize('mode', _MODE_TEMPLATES)
def test_mode_template_state_classes_have_matching_css(mode: str) -> None:
    """JS-orphan: every class JS toggles must be styled somewhere.

    A class added via ``element.classList.add('foo')`` should have *some*
    CSS rule that affects style, otherwise the class is decorative noise
    that misleads future readers and breaks the user-visible state.

    Allowed: classes defined in shared static/**.css (e.g. ``.correct``).
    Allowed: classes defined as a top-level ``.foo`` rule or compound
    ``.parent.foo`` rule in the mode's own ``mode_styles`` block.
    """
    path = TEMPLATES_DIR / f'{mode}.html'
    if not path.exists():
        pytest.skip(f'{mode}.html not present')

    text = path.read_text(encoding='utf-8')
    style_text = _extract_block(text, 'mode_styles')
    js_text = _extract_block(text, 'game_scripts')

    js_classes = _extract_js_toggled_classes(js_text)
    if not js_classes:
        return  # nothing to check for this mode

    mode_compound_states = {state for _parent, state in _extract_compound_selectors(style_text)}
    mode_top_level = _extract_top_level_classes(style_text)
    accounted_for = _SHARED_CSS_CLASSES | mode_compound_states | mode_top_level

    js_orphans = sorted(js_classes - accounted_for)
    assert not js_orphans, (
        f'{mode}.html: JS toggles classes that have no CSS rule anywhere — '
        f'{js_orphans}. Either (a) add a `.{{parent}}.{{class}}` rule in '
        f'mode_styles, or (b) confirm the class is shared (then nothing to do).'
    )


@pytest.mark.parametrize('mode', _MODE_TEMPLATES)
def test_mode_template_compound_css_rules_are_used(mode: str) -> None:
    """CSS-orphan: every `.parent.state` rule must have its `state` class
    actually set somewhere — by JS, by an Alpine binding, or by static
    template HTML.

    Decorative-only / shared state names (``active``, ``correct``,
    ``incorrect``, ``flipped``, ``matched``) are exempt because they are
    set generically by Alpine / shared JS components and a mode's `.parent.state`
    rule can legitimately re-skin them without the mode owning the state setter.
    """
    path = TEMPLATES_DIR / f'{mode}.html'
    if not path.exists():
        pytest.skip(f'{mode}.html not present')

    text = path.read_text(encoding='utf-8')
    style_text = _extract_block(text, 'mode_styles')
    js_text = _extract_block(text, 'game_scripts')

    compound = _extract_compound_selectors(style_text)
    if not compound:
        return  # nothing to check

    js_classes = _extract_js_toggled_classes(js_text)
    template_classes = _extract_template_html_classes(text)
    accounted_for = js_classes | template_classes | _SHARED_CSS_CLASSES

    orphans = sorted({
        f'.{parent}.{state}'
        for parent, state in compound
        if state not in accounted_for
    })
    assert not orphans, (
        f'{mode}.html: CSS rules style a state class that nothing ever sets — '
        f'{orphans}. Either remove the dead rule or wire the JS / template '
        f'to add the class.'
    )
