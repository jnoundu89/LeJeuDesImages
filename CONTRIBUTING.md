# Contributing

Thanks for your interest in Le Jeu Des Images! This guide will help you get started.

## Getting Started

```bash
# Fork and clone
git clone https://github.com/<your-user>/LeJeuDesImages.git
cd LeJeuDesImages

# Install dependencies (including dev tools)
uv sync --extra dev

# Set up config
cp config.example.yaml config.yaml
# Edit config.yaml with test data or use the /setup wizard

# Run the app
uv run python app.py
```

## Development Workflow

```bash
# Before coding
make lint          # Check code style
make test          # Run tests

# After coding
make lint          # Verify no regressions
make test          # Verify tests pass
git add <files>
git commit -m "type(scope): description"
```

## Commit Messages

Format: `type(scope): description`

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

Examples:
- `feat(modes): add trivia mode`
- `fix(scores): handle missing player_name`
- `refactor(templates): migrate quiz.html to extends`
- `docs: update DEPLOY.md with Fly.io guide`

## Adding a New Game Mode

This is the most common contribution. Modes are auto-discovered —
no registration, no list to edit — but they must declare a bit of
metadata so the UI (grid filters, previews, availability gate) can
render them without mode-by-mode conditionals.

### 1. Python model (`models/my_mode.py`)

```python
from typing import ClassVar, List
from flask_babel import lazy_gettext as _l
from .game_mode import GameMode

class MyMode(GameMode):
    # --- Declarative metadata ---------------------------------
    # Canonical fields every eligible employee MUST have populated.
    # If a dataset is missing any, the mode is automatically greyed
    # out on the selection grid with a "Complete the data" modal.
    required_fields: ClassVar[List[str]] = [
        'photo', 'first_name', 'last_name', 'sex',
    ]
    # Minimum eligible employees before the mode becomes playable.
    # Defaults to 10; override if your mode needs more (e.g.
    # position_match derives its value from the round layout).
    min_eligible_employees: ClassVar[int] = 10
    # Shown as 1 / 2 / 3 dots on the card.
    difficulty: ClassVar[int] = 2
    # Rough play time; drives the "~N min" badge on the card.
    estimated_duration_sec: ClassVar[int] = 120
    # Shown as tag chips on the card + in the filter bar. Keys must
    # be lowercase French (they're translated at render time by
    # routes.game_routes._tag_label).
    tags: ClassVar[List[str]] = ['photo', 'devinette']
    # Font Awesome v6 class.
    icon: ClassVar[str] = 'fa-puzzle-piece'
    # Preview animation on the card. Known values:
    #   'static'      → just the icon on a subtle gradient
    #   'pixelation'  → blurred avatar that sharpens on hover
    #   'silhouette'  → dark avatar that colorises on hover
    #   'scrambled'   → 3x3 tile grid that permutes on hover
    #   'emoji'       → three bouncing emoji cells
    #   'clue'        → three chips sliding in left-to-right
    #   'memory'      → two cards, one flipping
    #   'age'         → avatar with a rolling two-digit ticker
    #   'normal'      → avatar with tags (Tech / Alice D. / Dev)
    # See static/mode-previews.css + templates/_mode_preview.html.
    preview_type: ClassVar[str] = 'pixelation'
    # Multiplier on the default score (1 point per correct answer).
    # Clue / speed / progressive_hint use 3 to reward perfect runs.
    score_multiplier: ClassVar[int] = 1
    # Shows an "Expérimental" badge; reorder into the tail of the grid.
    experimental: ClassVar[bool] = False

    # --- Abstract API (required) -------------------------------
    @property
    def name(self): return 'my_mode'

    @property
    def description(self): return _l('My mode description')

    @property
    def display_name(self): return _l('My Mode')  # optional override

    @property
    def template(self): return 'my_mode.html'

    def get_question_data(self, data_id, used_indices, current_question):
        selected, current_question = self._pick_next_employee(
            data_id, used_indices, current_question
        )
        if selected.get('game_over'):
            return selected
        return {
            'game_over': False,
            'image_url': selected['photo'],
            'correct_name': self._make_full_name(selected),
            'name_choices': self._get_name_choices(selected),
            'current_question': current_question,
        }

    def update_score(self, user_id, **kwargs):
        if kwargs.get('correct_answer'):
            self.game_manager.score_manager.update_score(
                user_id, 1, stat_updates={'name': 1}
            )

    # --- Optional hooks ----------------------------------------
    # If your mode submits more than `correct_answer`, override
    # `_parse_answer` to read the extra form fields and pass them
    # to update_score. If your mode mutates the session on a
    # correct answer (e.g. memory adds to used_indices), override
    # `_session_updates_for`. If initialize needs extra keys,
    # override `_extra_init_data`. Those hooks let a fix in the
    # base class's `handle_answer` propagate to every mode.
```

No registration needed — `models.dataset.Dataset` auto-discovers
every `*_mode.py` module via `pkgutil.iter_modules`.

### 2. HTML template (`templates/my_mode.html`)

Extend `base_game.html` and fill the blocks. See
`templates/pixelation.html` for a simple example and
`templates/normal.html` for one that uses the full 3-column layout.
Keep styling to the `{% block mode_styles %}` block and rely on
`static/gameplay.css` for buttons, timer, progress bar, etc. —
don't hardcode colours, use design tokens (`var(--primary)`,
`var(--text)`, etc.) so the dataset's brand flows through.

### 3. Tests (optional but appreciated)

- Add the mode name to `tests/test_modes.py::ALL_MODES` — it runs
  the contract tests automatically (initialize returns required
  keys, first question isn't game_over, etc.).
- `tests/test_e2e.py` picks up the mode via `_MODE_NAMES` — add
  the name there too to get a browser smoke test.

### 4. Translations

Wrap all visible text:
- Templates: `{{ _('French text') }}`
- Python: `_l('French text')` for class-level strings (`display_name`, `description`)

Then run `make babel-extract && make babel-compile`. The source
locale is French; English translations live in
`translations/en/LC_MESSAGES/messages.po`.

## Theming a Dataset

Each dataset has a `theme` block that controls its visible color scheme. It pairs a preset palette with per-token overrides:

```yaml
datasets:
  acme:
    theme:
      palette: "midnight"          # one of the 16 built-in palettes
      overrides:
        primary: "#FF4D4D"         # override any of the 7 editable tokens
        surface: "#5B6A9C"
```

**Palettes** (see `models/config.py::PALETTES`): `corporate`, `slate`, `nordic`, `warm`, `sepia`, `sand`, `pastel`, `rose`, `mint`, `midnight`, `charcoal`, `ocean`, `forest`, `plum`, `dark`, `noir`. The palette sets six tokens (`bg`, `surface`, `surface-2`, `text`, `text-soft`, `border`) via `:root[data-palette="<key>"]` in `static/design-tokens.css`.

**Editable tokens** (see `models/config.py::EDITABLE_THEME_TOKENS`): `bg`, `surface`, `surface-2`, `text`, `text-soft`, `border`, `primary`. Any override outside this set is silently dropped; any value that isn't `#RRGGBB` is rejected. Overrides are emitted as inline CSS custom properties on `<html>` (see `app.py::_theme_inline_style` + `templates/base.html`), so inline specificity wins over the palette rule without touching `design-tokens.css`.

**Editing via the admin wizard**: go to `/setup` → *Ajouter un dataset* (or *Modifier*) → step 2 *Thème*. The token rows let you pick a palette first, then override individual tokens; the live preview and WCAG contrast meter update as you type. Clicking *Réinitialiser* next to a row drops the override and re-inherits from the palette.

**Back-compat**: legacy `company.primary_color` and `company.palette` are still read on load and migrated to `theme.overrides.primary` / `theme.palette` on next save.

## Conventions

- **Python**: PEP 8, enforced by ruff. Single quotes preferred.
- **Employee data**: Always use canonical field names (`first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`). Never reference CSV column names directly.
- **Templates**: Must extend a base template. All text uses `_()`.
- **No company data in code**: Company names, emails, logos come from `config.yaml` only (or the `/setup` wizard).
- **Config files**: `config.yaml` is gitignored. Only `config.example.yaml` is committed.
- **Dataset filesystem layout**: each dataset lives under `data/<id>/` with three files: `team.csv`, `photos/`, `scores.json`. The admin wizard enforces this layout; don't hand-create datasets in other locations.
- **Dataset IDs**: lowercase, alphanumeric + `_-`, 1-32 chars. Validated server-side at save time.
- **Per-request dataset resolution**: in routes, call `registry.current(request)` to get the active `Dataset`. Never cache a `Dataset` reference across requests — the user may switch datasets at any moment via the `dataset` cookie.

## Project Structure

See `CLAUDE.md` for a complete architecture overview.

## Questions?

Open an issue on GitHub. We're happy to help!
