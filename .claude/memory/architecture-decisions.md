---
name: Architecture decisions
description: Key architectural choices and their rationale - consult before proposing changes
type: project
---

## Company-agnostic via config.yaml (not admin DB, not multi-tenant)

The game uses a YAML config file for company branding + CSV column mapping. This was chosen over an admin database (too complex for an internal game) and multi-tenant (over-engineering). The `/setup` wizard writes to `config.yaml`.

**How to apply:** Never hardcode company-specific data. Always read from `CompanyConfig`.

## Column mapping at load time (not at access time)

CSV columns are renamed to canonical names ONCE in `EmployeeData.__init__()` via `DataFrame.rename()`. All downstream code uses canonical names only.

**How to apply:** Never reference original CSV column names in models, routes, or templates. Only canonical: `first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`, `birth_date`, `contract_start`, `manager_name`.

## Auto-discovery for game modes (not manual registration)

`app.py` uses `pkgutil.iter_modules` to find `GameMode` subclasses. Adding a mode = creating a file. No import or registration needed.

**How to apply:** Never add imports or `register_mode()` calls to `app.py` for new modes.

## Generic /check route via handle_answer() (not if-elif per mode)

The `/check` route calls `mode.handle_answer(user_id, form_data, session)`. Each mode parses its own form fields.

**How to apply:** Never add mode-specific logic to `game_routes.py`. Override `handle_answer()` in the mode class instead.

## Template inheritance with 3 bases (not standalone templates)

All templates extend one of: `base.html`, `base_page.html`, `base_game.html`.

**How to apply:** New templates must extend the appropriate base. Never create standalone HTML documents.

## TinyDB for scores (not SQLite/PostgreSQL)

TinyDB was chosen for simplicity (zero setup, JSON file). Adequate for < 500 players. If scaling needed, migrate to SQLite.

**How to apply:** All score operations go through `ScoreManager`. The storage backend is encapsulated.
