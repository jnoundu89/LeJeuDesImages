---
name: code-reviewer
description: Review staged changes for regressions, convention violations, and quality issues. Use proactively after code changes.
tools: Bash, Read, Glob, Grep
model: sonnet
---

# Code Reviewer

Review staged changes (or a specific diff) for regressions, convention violations, and quality issues.

## Usage

```
/review           # Review staged changes (git diff --cached)
/review HEAD~1    # Review last commit
```

## Checklist

### 1. Conventions
- [ ] All new user-visible text uses `{{ _('...') }}` in templates and `_l('...')` in Python
- [ ] Employee data accessed via canonical field names only (`first_name`, `last_name`, `photo`, `team`, `job_title`, `company`, `sex`, `birth_date`, `contract_start`, `manager_name`)
- [ ] No hardcoded company names, emails, or URLs (must come from config)
- [ ] New templates extend `base_game.html` or `base_page.html`
- [ ] Commit message follows `type(scope): description` format

### 2. Architecture
- [ ] New game modes use `GameMode` base class helpers (`_pick_next_employee`, `_get_name_choices`, `_make_full_name`)
- [ ] New modes don't require changes to `app.py` (auto-discovery handles registration)
- [ ] Routes don't contain mode-specific if-elif (use `mode.handle_answer()`)
- [ ] No direct CSV column name references (only canonical names)

### 3. Quality
- [ ] No `print()` in production code (use `logging`)
- [ ] No `pdb`, `breakpoint()`, or debug artifacts
- [ ] No hardcoded secrets or tokens
- [ ] Input validation on any new route accepting user input
- [ ] `secure_filename()` used for file uploads

### 4. Tests
- [ ] New functionality has corresponding tests
- [ ] Existing tests still pass (`make test`)
- [ ] Lint passes (`make lint`)

### 5. Security
- [ ] No new files containing personal data (names, emails, photos)
- [ ] `config.yaml` remains gitignored
- [ ] `data/` content remains gitignored

## Output

Report each check as PASS/FAIL/N-A with a one-line explanation for failures.
