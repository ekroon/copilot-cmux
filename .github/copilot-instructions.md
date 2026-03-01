# Copilot Instructions

## Architecture

This is a **Copilot CLI plugin** (`copilot-cmux`) that bridges Copilot CLI hook events to [cmux](https://cmux.dev) workspace sidebar updates and macOS notifications.

The plugin is structured as a monorepo with a marketplace wrapper:

- `.github/plugin/marketplace.json` — marketplace metadata pointing at `plugins/` root. The `version` field here must be updated separately from `plugin.json` when publishing.
- `plugins/copilot-cmux/plugin.json` — plugin manifest (name, version, repository URL). The `repository` field is required for `copilot plugin update` to work.
- `plugins/copilot-cmux/hooks.json` — maps Copilot CLI hook events (`sessionStart`, `preToolUse`, `sessionEnd`) to the Python handler.
- `plugins/copilot-cmux/scripts/cmux_notify.py` — single-file handler that implements all logic.

## Hook event flow

All three hooks invoke the same script (`cmux_notify.py`) with the event name as `argv[1]` and the hook payload on stdin (JSON).

- **`sessionStart`** → clears previous state, signals `cmux claude-hook session-start`, sets running indicator.
- **`preToolUse`** → dispatches by tool name:
  - `report_intent` → updates sidebar title and intent status silently.
  - Interactive tools (`ask_user`, `exit_plan_mode`) → sets attention indicator + popup notification (unless the caller surface is focused).
  - Other tools → clears attention indicator.
- **`sessionEnd`** → updates sidebar, clears indicators, signals `cmux claude-hook stop`, removes temp state file.

## Key conventions

- **State persistence**: per-session state is stored in a temp file keyed by `CMUX_WORKSPACE_ID` env var (`/tmp/cmux-copilot-<safe_ref>.json`). State tracks whether session-start was signaled and the last workspace title to avoid redundant updates.
- **cmux binary resolution**: prefers the bundled path `/Applications/cmux.app/Contents/Resources/bin/cmux`, falls back to `$PATH`. If cmux is unavailable, falls back to `osascript` for macOS notifications. If neither exists, the hook exits silently (never fails the hook).
- **Subprocess calls**: all cmux/osascript calls use 2–3 second timeouts, `check=False`, and `capture_output=True`. Failures are swallowed — the plugin must never block or break the Copilot CLI session.
- **No external dependencies**: the script uses only Python stdlib. No `requirements.txt` or virtualenv needed.
- **Payload extraction**: uses a defensive BFS approach (`find_first_string`) to locate fields in the hook payload, supporting both camelCase and snake_case key variants.

## Install & test locally

```bash
# Install from GitHub
copilot plugin install ekroon/copilot-cmux

# Test the script directly (pipe JSON payload on stdin)
echo '{"toolName":"report_intent","toolArgs":{"intent":"Testing"}}' | \
  python3 plugins/copilot-cmux/scripts/cmux_notify.py preToolUse
```

## Version management

Two version fields must stay in sync when releasing:

1. `plugins/copilot-cmux/plugin.json` → `"version"` (source of truth)
2. `.github/plugin/marketplace.json` → `plugins[0].version` (marketplace listing)
