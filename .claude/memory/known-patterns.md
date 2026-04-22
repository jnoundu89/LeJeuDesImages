---
name: Known patterns and pitfalls
description: Patterns that work, patterns that don't - consult before implementing
type: feedback
---

## GameMode helpers reduce mode files by 60%

The base class provides `_pick_next_employee()`, `_get_name_choices()`, `_make_full_name()`. Simple modes (pixelation, mirror, silhouette, etc.) should be 30-50 lines using these helpers.

**Why:** Before refactoring, 17 modes had 70-90% identical boilerplate. Bug fixes had to be replicated across files.

**How to apply:** Always check if a base helper exists before writing custom logic in a new mode.

## Flask blueprint registration is NOT idempotent

Calling `create_app()` twice causes `AssertionError` because `init_routes()` registers routes on an already-registered blueprint. The smoke tests use `from app import app` (module-level instance) not `create_app()`.

**Why:** Discovered during Phase 0 when tests failed.

**How to apply:** Tests must use the `app` fixture from `conftest.py` (session-scoped). Never call `create_app()` directly in tests.

## pandas 2.1.0 doesn't compile on Python 3.13

The `pyproject.toml` uses `pandas>=2.2` to avoid build failures. Don't pin back to 2.1.0.

**Why:** Cython/numpy ABI incompatibility with Python 3.13.

## i18n: use _l() for class-level strings, _() for function-level

`lazy_gettext` (`_l`) is required for strings evaluated at import time (mode descriptions as properties). Regular `gettext` (`_`) works in request context (templates, route handlers).

**Why:** Regular `_()` fails outside request context because there's no locale set yet.

## Score stat_updates is a flexible dict

The old API used 4 keyword args (`company_correct`, `team_correct`, etc.). The new API uses `stat_updates={'name': 1, 'team': 1}`. Backwards-compatible with legacy records.

**How to apply:** Always use `stat_updates` dict, never the old 4-param signature.
