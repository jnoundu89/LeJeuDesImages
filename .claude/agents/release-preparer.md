---
name: release-preparer
description: Verify the project is clean and ready for a release or public commit
tools: Bash, Read, Grep, Glob
model: sonnet
---

# Release Preparer

Verify the project is clean and ready for a release or public commit.

## Usage

```
/release-preparer
```

## Checks

### 1. No confidential data
- `grep -ri "infolegale\|eloficash\|ilucca\|@infolegale" models/ routes/ templates/ static/` returns 0 results
- `config.yaml` is not tracked (`git ls-files config.yaml` returns nothing)
- `data/` content is gitignored
- `static/images/` is gitignored
- No hardcoded auth tokens, API keys, or passwords in tracked files

### 2. Code quality
- `make lint` passes (ruff, zero errors)
- `make test` passes (all tests green)
- No `print()` statements left in production code (use `logging`)
- No `pdb` or `breakpoint()` calls left

### 3. i18n completeness
- Run `make babel-extract`
- Check `translations/en/LC_MESSAGES/messages.po` for empty msgstr entries
- All visible French text in templates uses `{{ _('...') }}`
- All mode descriptions use `_l('...')`

### 4. Documentation
- `README.md` is up to date (stack, setup instructions, game modes list)
- `CLAUDE.md` reflects current architecture
- `DEPLOY.md` deployment instructions are valid
- `docs/data-format.md` matches the current canonical fields
- `config.example.yaml` has all required fields

### 5. Git state
- Working tree is clean (`git status` shows nothing)
- All changes are committed
- Branch is up to date with remote

### 6. Dependencies
- `pyproject.toml` lists all dependencies
- `uv.lock` is up to date (`uv sync` makes no changes)
- No unused dependencies

## Output

Report a checklist with pass/fail for each check. Flag any issues that need fixing before release.
