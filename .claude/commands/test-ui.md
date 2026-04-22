---
name: test-ui
description: Run UI tests with Playwright MCP (smoke, game flow, admin wizard, responsive)
---

# Test UI

Uses the Playwright MCP server to verify the game works in the browser.

## Quick start

1. Start the app: `uv run python app.py &` (wait for "Running on...")
2. Run UI scenarios using `mcp__playwright__*` tools
3. Follow the full procedure in `.claude/agents/ui-tester.md`

## Scenarios

- **smoke**: All pages load (`/`, `/about`, `/how-to-play`, `/scores`, `/setup`)
- **game**: Full pixelation mode flow (start -> answer -> next -> result)
- **admin**: Setup wizard steps 1-4
- **responsive**: Screenshots at desktop (1920x1080), tablet (768x1024), mobile (375x667)

Kill the app after: `pkill -f "python app.py"`
