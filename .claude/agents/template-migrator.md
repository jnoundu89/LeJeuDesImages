---
name: template-migrator
description: Migrate a standalone HTML template to use extends with a base template
tools: Read, Edit, Bash, Grep, Glob
---

# Template Migrator

Migrate a standalone HTML template to use `{% extends %}` with the appropriate base template.

## Usage

```
/template-migrator <template_name>
```

Example: `/template-migrator card_game`

## Steps

1. **Read the target template** (`templates/<template_name>.html`) fully
2. **Identify the base to extend**:
   - Game mode with 3-column layout (stats, center, scores) -> `base_game.html`
   - Navigation page (header, footer, music player) -> `base_page.html`
   - Completely unique layout -> `base.html`
3. **Read the base template** to understand available blocks
4. **Decompose the template**:
   - What is duplicated from the base (HTML shell, CSS links, layout structure)
   - What is unique (mode-specific styles, content, scripts)
5. **Rewrite** using `{% extends %}` with only the unique blocks:
   - `{% block mode_styles %}` for inline CSS
   - `{% block game_title %}` for the h1
   - `{% block game_content %}` for the main area
   - `{% block game_choices %}` for answer buttons
   - `{% block game_scripts %}` for JavaScript
   - `{% block form_fields %}` for hidden inputs
6. **Preserve ALL functionality**: every CSS class, ID, JS function, form field
7. **Wrap French text** in `{{ _('...') }}` if not already done
8. **Verify**:
   - `make test` passes
   - `make lint` passes
   - Template parses correctly (no Jinja2 syntax errors)

## Base templates reference

### base_game.html blocks
`lang`, `title`, `extra_css`, `mode_styles`, `game_title`, `progress_bar`, `game_content`, `after_timer`, `score_display`, `form_attrs`, `form_fields`, `game_choices`, `game_scripts`

### base_page.html blocks
`lang`, `title`, `meta`, `page_title`, `page_tagline`, `content`, `before_music_player`

### base.html blocks
`lang`, `title`, `meta`, `extra_css`, `body`, `scripts`

## Reference: already-migrated templates
- Simple game mode: `templates/pixelation.html`
- Complex game mode: `templates/index.html`
- Page template: `templates/mode_selection.html`
- Unique layout: `templates/result.html`
