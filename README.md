# cmux-notify Copilot CLI plugin

This plugin sends Copilot CLI hook notifications to `cmux notify` with a macOS `osascript` fallback.

## Triggers

- **Workspace status**: `preToolUse` events for `report_intent` update the cmux sidebar in real time:
  - **Title** → `"project — session goal"` (via `cmux rename-workspace`, updates when session title changes)
  - **Subtitle** → current intent text (via `cmux claude-hook notification`, updates on every intent change)
  - **Status indicator** → `⚡️ running` (via `cmux claude-hook session-start` on first intent)
- **Needs input/action**: `preToolUse` events for interaction-required prompts (e.g., `ask_user`, `exit_plan_mode`, or payloads with interaction markers like `question`, `choices`, `actions`).
- **Finished / stopped**: `sessionEnd` events (`complete`, `error`, `abort`, `timeout`, `user_exit`). Updates the subtitle and signals `cmux claude-hook stop`.

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
copilot plugin uninstall cmux-notify
copilot plugin install ekroon/copilot-cmux
```

Uninstall:

```bash
copilot plugin uninstall cmux-notify
```

## Behavior

1. On every `report_intent` tool call, the plugin updates the cmux workspace sidebar:
   - Renames the workspace to `"<project> — <session title>"` (only when the title changes).
   - Sets the subtitle to the current intent (e.g., "Fixing auth bug", "Running tests").
   - On the first intent of a session, signals `cmux claude-hook session-start` to show the `⚡️ running` indicator.
2. If `cmux` is available, the plugin runs:
   - `cmux notify --title "Copilot CLI" --subtitle ... --body ...`
3. Subtitle prefers context in the form `"<session title> — <project>"`; if context is unavailable it falls back to event labels.
4. For interaction-required `preToolUse` prompts and `sessionEnd`, if cmux is frontmost and the caller surface is already focused, notification is skipped.
5. On `sessionEnd`, the subtitle is updated to the end reason and `cmux claude-hook stop` is signaled.
6. If `cmux` is unavailable or fails and `osascript` exists, it sends a macOS notification.
7. If neither tool exists, it exits without failing the hook.
