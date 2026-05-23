---
name: ui-tester
description: Verify the game works in the browser using Playwright MCP
tools: Bash, Read, mcp__playwright__*
---

# UI Tester (Playwright MCP)

Verify the game works in the browser using the Playwright MCP server.

## Prerequisites

The Flask app must be running locally. Start it with:

```bash
uv run python app.py &
```

Wait for "Running on http://127.0.0.1:5000" before proceeding.

The Playwright MCP tools are available as `mcp__playwright__*`.

## Usage

```
/test-ui              # Run all UI scenarios
/test-ui smoke        # Pages load correctly
/test-ui game         # Full game flow
/test-ui admin        # Setup wizard
/test-ui responsive   # Screenshots at different viewports
```

## Scenario 1: Smoke UI (pages load)

Verify these pages load without errors:

1. Navigate to `http://127.0.0.1:5000/` -- mode selection page
   - Assert: page title contains "Jeu Des Images"
   - Assert: at least one mode card is visible
2. Navigate to `/about`
   - Assert: page loads, contains company name
3. Navigate to `/how-to-play`
   - Assert: page loads
4. Navigate to `/scores`
   - Assert: page loads, shows score cards
5. Navigate to `/setup`
   - Assert: setup wizard loads with Step 1 visible

For each page, take a screenshot for visual verification.

## Scenario 2: Full game flow

Test the pixelation mode end-to-end:

1. Navigate to `http://127.0.0.1:5000/`
2. Click on the "Pixelation" mode card's "Jouer maintenant" button
3. Assert: game page loads with a pixelated image
4. Assert: 4 name choice buttons are visible
5. Click one of the choice buttons
6. Assert: answer feedback is shown (correct/incorrect styling)
7. Click "Personne suivante" button
8. Assert: next question loads (new image)
9. Take screenshot of the game in progress

## Scenario 3: Admin wizard

Test the full setup wizard flow across all 4 steps.

### Step 1: Branding

1. Navigate to `http://127.0.0.1:5000/setup`
2. Assert: Step 1 panel (`#step-1`) is visible
3. Assert: stepper indicator `[data-step="1"]` has class `active`
4. Assert: inputs are present: `#company-name`, `#logo-url`, `#contact-email`, `#tagline`
5. Fill in: company name = "Test Company", logo URL = "https://example.com/logo.png", email = "test@example.com", tagline = "Know your team!"
6. Take screenshot
7. Click "Suivant" button to go to Step 2

### Step 2: Employee Data

8. Assert: Step 2 panel (`#step-2`) is visible, Step 1 is hidden
9. Assert: stepper indicator `[data-step="1"]` has class `completed`
10. Assert: stepper indicator `[data-step="2"]` has class `active`
11. Assert: CSV drop zone (`#csv-drop-zone`) is visible with file input
12. Assert: upload status area (`#csv-upload-status`) exists
13. Assert: CSV preview (`#csv-preview`) is initially hidden
14. Assert: mapping section (`#mapping-section`) is initially hidden
15. Take screenshot
16. Click "Suivant" to go to Step 3

### Step 3: Photos

17. Assert: Step 3 panel (`#step-3`) is visible
18. Assert: ZIP drop zone (`#photos-drop-zone`) is visible
19. Assert: info note (`.photos-note`) about manual photo placement is visible
20. Take screenshot
21. Click "Suivant" to go to Step 4 (this also calls `buildSummary()`)

### Step 4: Summary & Save

22. Assert: Step 4 panel (`#step-4`) is visible
23. Assert: summary tables exist (`#summary-company`, `#summary-data`, `#summary-mapping`)
24. Assert: company summary shows the values entered in Step 1 ("Test Company", etc.)
25. Take screenshot
26. Click "Sauvegarder la configuration" button (`#save-btn`)
27. Assert: toast notification appears (`.toast.show`)
28. Take screenshot of the toast

### Navigation & state persistence

29. Click on stepper indicator `[data-step="1"]` to go back to Step 1
30. Assert: Step 1 panel is visible again
31. Assert: `#company-name` still has value "Test Company"
32. Assert: `#contact-email` still has value "test@example.com"
33. Click on stepper indicator `[data-step="2"]` to go to Step 2
34. Assert: Step 2 panel is visible
35. Click "Precedent" button to go back to Step 1
36. Assert: Step 1 panel is visible

### Responsive

37. Resize to mobile (375x667), navigate to `/setup`, take screenshot
38. Assert: stepper wraps properly, form is readable, buttons are tappable
39. Resize to tablet (768x1024), navigate to `/setup`, take screenshot
40. Resize back to desktop (1920x1080)

## Scenario 4: Responsive screenshots

Take screenshots at different viewports:

1. **Desktop** (1920x1080): `/`, `/about`, game page
2. **Tablet** (768x1024): `/`, game page
3. **Mobile** (375x667): `/`, game page

For each, use Playwright's viewport resize then navigate and screenshot.

## MCP Tools Reference

Key Playwright MCP tools to use:
- `mcp__playwright__browser_navigate` -- navigate to URL
- `mcp__playwright__browser_click` -- click an element (by text, selector, or coordinates)
- `mcp__playwright__browser_screenshot` -- take a screenshot
- `mcp__playwright__browser_type` -- type into an input field
- `mcp__playwright__browser_select_option` -- select from a dropdown
- `mcp__playwright__browser_wait_for_text` -- wait for text to appear
- `mcp__playwright__browser_resize` -- resize viewport

## After testing

Kill the background Flask process:

```bash
kill %1  # or: pkill -f "python app.py"
```

Report results as a checklist with pass/fail for each scenario, including screenshots taken.
