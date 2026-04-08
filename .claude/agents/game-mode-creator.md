# Game Mode Creator

Create a complete new game mode from scratch: Python model, HTML template, i18n strings, and tests.

## Usage

```
/game-mode-creator <mode_name> "<description>"
```

Example: `/game-mode-creator emoji_battle "Two emoji sets compete, guess which represents the employee"`

## Steps

1. **Validate input**: Check that `<mode_name>` is snake_case and doesn't already exist in `models/`
2. **Create the model** (`models/<mode_name>_mode.py`):
   - Import `GameMode`, `lazy_gettext as _l`
   - Class name: CamelCase version of mode_name + `Mode` (e.g., `EmojiBattleMode`)
   - Properties: `name`, `description` (wrapped in `_l()`), `template`
   - Use base class helpers: `_pick_next_employee()`, `_get_name_choices()`, `_make_full_name()`
   - Implement `get_question_data()` and `update_score()`
   - If the mode needs custom form parsing, override `handle_answer()`
3. **Create the template** (`templates/<mode_name>.html`):
   - Extend `base_game.html`
   - Fill blocks: `title`, `mode_styles`, `game_title`, `game_content`, `game_choices`, `game_scripts`
   - All visible text wrapped in `{{ _('...') }}`
4. **Add i18n strings**:
   - Run `make babel-extract`
   - Add English translations to `translations/en/LC_MESSAGES/messages.po`
   - Run `make babel-compile`
5. **Create tests** (`tests/test_<mode_name>_mode.py`):
   - Test `initialize()` returns expected keys
   - Test `get_question_data()` returns expected structure
   - Test `update_score()` updates correctly
6. **Verify**:
   - `make lint` passes
   - `make test` passes (all tests including new ones)
   - Auto-discovery picks up the new mode (check with smoke test)

## Canonical field names

Always use: `first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`, `birth_date`, `contract_start`, `manager_name`

## Reference files

- Base class with helpers: `models/game_mode.py`
- Simple mode example: `models/pixelation_mode.py`
- Complex mode example: `models/clue_mode.py`
- Template example: `templates/pixelation.html`
- Test example: `tests/test_game_mode.py`
