"""macOS AppleScript execution (architecture router order: AppleScript first)."""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass

# Common aliases → Application names for ``open`` fast path.
APP_ALIASES: dict[str, str] = {
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "safari": "Safari",
    "finder": "Finder",
    "terminal": "Terminal",
    "notes": "Notes",
    "mail": "Mail",
}


@dataclass
class AppleScriptResult:
    success: bool
    message: str


def resolve_app_name(name: str) -> str:
    key = name.strip().lower()
    return APP_ALIASES.get(key, name.strip())


def open_application(app_name: str) -> AppleScriptResult:
    """
    Activate a macOS application via AppleScript.

    Returns a result object; does not raise on script failure.
    """
    if platform.system() != "Darwin":
        return AppleScriptResult(success=False, message="AppleScript only supported on macOS")

    resolved = resolve_app_name(app_name)
    script = f'tell application "{resolved}" to activate'

    try:
        completed = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return AppleScriptResult(success=False, message=str(exc))

    if completed.returncode != 0:
        err = (completed.stderr or completed.stdout or "osascript failed").strip()
        return AppleScriptResult(success=False, message=err)

    return AppleScriptResult(success=True, message=f"Opened {resolved}")
