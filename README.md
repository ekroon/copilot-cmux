# cmux-notify Copilot CLI plugin

This plugin sends Copilot CLI hook notifications to `cmux notify` with a macOS `osascript` fallback.

## Triggers

- **Needs input/action**: `preToolUse` events for interaction-required prompts (e.g., `ask_user`, `exit_plan_mode`, or payloads with interaction markers like `question`, `choices`, `actions`).
- **Finished / stopped**: `sessionEnd` events (`complete`, `error`, `abort`, `timeout`, `user_exit`).

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

1. If `cmux` is available, the plugin runs:
   - `cmux notify --title "Copilot CLI" --subtitle ... --body ...`
2. Subtitle prefers context in the form `"<session title> — <project>"`; if context is unavailable it falls back to event labels.
3. For interaction-required `preToolUse` prompts and `sessionEnd`, if cmux is frontmost and the caller surface is already focused, notification is skipped.
4. If `cmux` is unavailable or fails and `osascript` exists, it sends a macOS notification.
5. If neither tool exists, it exits without failing the hook.
