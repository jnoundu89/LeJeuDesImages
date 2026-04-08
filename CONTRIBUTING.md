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

This is the most common contribution. You need 2 files:

### 1. Python model (`models/my_mode.py`)

```python
from flask_babel import lazy_gettext as _l
from .game_mode import GameMode

class MyMode(GameMode):
    @property
    def name(self): return 'my_mode'

    @property
    def description(self): return _l('My mode description')

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
```

No registration needed -- auto-discovery picks it up.

### 2. HTML template (`templates/my_mode.html`)

Extend `base_game.html` and fill the blocks. See `templates/pixelation.html` for a simple example.

### 3. Tests (optional but appreciated)

Add `tests/test_my_mode.py`. See `tests/test_game_mode.py` for patterns.

### 4. Translations

Wrap all visible text:
- Templates: `{{ _('French text') }}`
- Python: `_l('French text')` for class-level strings

Then run `make babel-extract && make babel-compile`.

## Conventions

- **Python**: PEP 8, enforced by ruff. Single quotes preferred.
- **Employee data**: Always use canonical field names (`first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`). Never reference CSV column names directly.
- **Templates**: Must extend a base template. All text uses `_()`.
- **No company data in code**: Company names, emails, logos come from `config.yaml` only.
- **Config files**: `config.yaml` is gitignored. Only `config.example.yaml` is committed.

## Project Structure

See `CLAUDE.md` for a complete architecture overview.

## Questions?

Open an issue on GitHub. We're happy to help!
