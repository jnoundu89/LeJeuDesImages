---
name: add-game-mode
description: Create a complete new game mode (model + template + tests + i18n)
---

# Add Game Mode

When the user asks to create a new game mode, follow the game-mode-creator agent instructions at `.claude/agents/game-mode-creator.md`.

Quick reference for the model file:

```python
from flask_babel import lazy_gettext as _l
from .game_mode import GameMode

class MyMode(GameMode):
    @property
    def name(self): return 'my_mode'

    @property
    def description(self): return _l('Description')

    @property
    def template(self): return 'my_mode.html'

    def get_question_data(self, data_id, used_indices, current_question):
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
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
            self.game_manager.score_manager.update_score(user_id, 1, stat_updates={'name': 1})
```

Template extends `base_game.html`. All text uses `{{ _('...') }}`. Run `make test && make lint` after.
