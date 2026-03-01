# copilot-cmux Copilot CLI plugin

This plugin sends Copilot CLI hook notifications to `cmux notify` with a macOS `osascript` fallback.

## Triggers

- **Workspace status**: `preToolUse` events for `report_intent` update the cmux sidebar silently:
  - **Title** → `"project — session goal"` (via `cmux rename-workspace`, updates when session title changes)
  - **Sidebar status** → current intent text (via `cmux set-status intent`, updates on every intent change)
  - **Status indicator** → `⚡️ running` (via `cmux claude-hook session-start` on first intent)
  - Clears any previous attention indicator when the agent resumes working
- **Needs input/action**: `preToolUse` events for interaction-required prompts (e.g., `ask_user`, `exit_plan_mode`):
  - Sets a `🔔 attention` sidebar status (via `cmux set-status attention --icon bell.fill`)
  - Sends a `cmux notify` popup notification (unless the caller surface is already focused)
- **Finished / stopped**: `sessionEnd` events (`complete`, `error`, `abort`, `timeout`, `user_exit`). Updates the sidebar status and signals `cmux claude-hook stop`.

## Files

- `plugin.json` — plugin manifest.
- `hooks.json` — hook bindings.
- `scripts/cmux_notify.py` — notification handler.

## Install (GitHub)

```bash
copilot plugin install ekroon/copilot-cmux
copilot plugin list
```

Update to the latest GitHub version:

```bash
copilot plugin uninstall copilot-cmux
copilot plugin install ekroon/copilot-cmux
```

Uninstall:

```bash
copilot plugin uninstall copilot-cmux
```

## Behavior

1. On every `report_intent` tool call, the plugin updates the cmux workspace sidebar silently:
   - Renames the workspace to `"<project> — <session title>"` (only when the title changes).
   - Sets the sidebar status to the current intent (e.g., "Fixing auth bug", "Running tests") via `cmux set-status`.
   - On the first intent of a session, signals `cmux claude-hook session-start` to show the `⚡️ running` indicator.
   - Clears any previous attention indicator when the agent resumes working.
2. For interaction-required `preToolUse` prompts (`ask_user`, `exit_plan_mode`):
   - Sets a `🔔 attention` indicator in the sidebar via `cmux set-status attention --icon bell.fill`.
   - Sends a `cmux notify` popup notification (skipped if the caller surface is already focused).
3. Sidebar status prefers context in the form `"<session title> — <project>"`; if context is unavailable it falls back to event labels.
4. On `sessionEnd`, the sidebar status is updated to the end reason and `cmux claude-hook stop` is signaled.
5. If `cmux` is unavailable or fails and `osascript` exists, it sends a macOS notification for actionable events.
6. If neither tool exists, it exits without failing the hook.
