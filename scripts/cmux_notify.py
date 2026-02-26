#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys

MAX_BODY_LENGTH = 180


def parse_hook_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        print(f"cmux-notify: invalid hook payload: {error}", file=sys.stderr)
        return {}
    return data if isinstance(data, dict) else {}


def normalize_body(text: str) -> str:
    return " ".join(text.split())[:MAX_BODY_LENGTH]


def resolve_cmux_binary():
    preferred_cmux = "/Applications/cmux.app/Contents/Resources/bin/cmux"
    if os.path.isfile(preferred_cmux) and os.access(preferred_cmux, os.X_OK):
        return preferred_cmux
    return shutil.which("cmux")


def is_caller_surface_focused(cmux: str) -> bool:
    try:
        result = subprocess.run(
            [cmux, "identify", "--json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False

    if result.returncode != 0 or not result.stdout.strip():
        return False

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False

    if not isinstance(data, dict):
        return False

    focused = data.get("focused")
    caller = data.get("caller")
    if not isinstance(focused, dict) or not isinstance(caller, dict):
        return False

    focused_surface = focused.get("surface_ref")
    caller_surface = caller.get("surface_ref")
    focused_workspace = focused.get("workspace_ref")
    caller_workspace = caller.get("workspace_ref")
    return (
        isinstance(focused_surface, str)
        and isinstance(caller_surface, str)
        and focused_surface == caller_surface
        and isinstance(focused_workspace, str)
        and isinstance(caller_workspace, str)
        and focused_workspace == caller_workspace
    )


def is_cmux_frontmost() -> bool:
    osascript = shutil.which("osascript")
    if not osascript:
        return False

    expected_bundle = (os.environ.get("CMUX_BUNDLE_ID") or "com.cmuxterm.app").strip()
    if not expected_bundle:
        return False

    script = 'tell application "System Events" to get bundle identifier of first process whose frontmost is true'
    try:
        result = subprocess.run(
            [osascript, "-e", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False

    return result.returncode == 0 and result.stdout.strip() == expected_bundle


def is_same_cmux_surface_active() -> bool:
    cmux = resolve_cmux_binary()
    return bool(cmux and is_cmux_frontmost() and is_caller_surface_focused(cmux))


def extract_tool_name(payload: dict) -> str:
    for key in ("toolName", "tool_name"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def extract_tool_args(payload: dict) -> dict:
    for key in ("toolArgs", "tool_args", "arguments"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
    return {}


def notification_from_tool_use(payload: dict):
    if extract_tool_name(payload) != "ask_user":
        return None

    if is_same_cmux_surface_active():
        return None

    question = ""
    tool_args = extract_tool_args(payload)
    question_value = tool_args.get("question")
    if isinstance(question_value, str):
        question = normalize_body(question_value)

    body = question or "Copilot needs your input."
    return ("Copilot CLI", "Needs answer", body)


def notification_from_session_end(payload: dict):
    if is_same_cmux_surface_active():
        return None

    reason = str(payload.get("reason") or "unknown")
    if reason == "complete":
        body = "Task finished."
    else:
        body = f"Task stopped ({reason})."
    return ("Copilot CLI", "Session ended", body)


def build_notification(event_name: str, payload: dict):
    if event_name in ("preToolUse", "postToolUse"):
        return notification_from_tool_use(payload)
    if event_name == "sessionEnd":
        return notification_from_session_end(payload)
    return None


def notify(title: str, subtitle: str, body: str) -> None:
    cmux = resolve_cmux_binary()
    if cmux:
        command = [cmux, "notify", "--title", title]
        if subtitle:
            command.extend(["--subtitle", subtitle])
        if body:
            command.extend(["--body", body])
        try:
            result = subprocess.run(command, check=False, timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            result = None
        if result and result.returncode == 0:
            return

    osascript = shutil.which("osascript")
    if osascript:
        script = f"display notification {json.dumps(body)} with title {json.dumps(title)}"
        if subtitle:
            script += f" subtitle {json.dumps(subtitle)}"
        subprocess.run([osascript, "-e", script], check=False)


def main() -> int:
    event_name = sys.argv[1] if len(sys.argv) > 1 else ""
    payload = parse_hook_payload()
    notification = build_notification(event_name, payload)
    if not notification:
        return 0
    notify(*notification)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
