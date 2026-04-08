---
name: check-release
description: Verify project is clean and ready for release (no secrets, tests pass, i18n complete)
---

# Check Release

Run the full release checklist from `.claude/agents/release-preparer.md`:

1. `grep -ri "infolegale\|eloficash\|ilucca" models/ routes/ templates/ static/*.js` -> must be empty
2. `git ls-files config.yaml` -> must be empty (gitignored)
3. `make lint` -> must pass
4. `make test` -> must pass
5. `make babel-extract` then check for empty msgstr in EN catalog
6. `git status` -> must be clean
7. `uv sync` -> must make no changes

Report a pass/fail checklist.
