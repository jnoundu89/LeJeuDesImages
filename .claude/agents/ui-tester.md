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

Test the setup wizard flow:

1. Navigate to `http://127.0.0.1:5000/setup`
2. Assert: Step 1 (Company Branding) is visible
3. Fill in company name: "Test Company"
4. Fill in logo URL: "https://example.com/logo.png"
5. Click "Next" to go to Step 2
6. Assert: Step 2 (Employee Data) is visible
7. Take screenshot of each step

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
