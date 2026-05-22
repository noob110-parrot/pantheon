"""Allowlisted shell execution (plan.json tool_permissions.terminal_allowlist)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class ShellResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int


def is_allowlisted(command: str, allowlist: list[str]) -> bool:
    """True when ``command`` exactly matches an allowlisted entry."""
    normalized = " ".join(command.strip().split())
    return normalized in allowlist


def run_allowlisted(command: str, allowlist: list[str], *, timeout_seconds: int = 30) -> ShellResult:
    """
    Run a shell command only if it exactly matches the allowlist.

    Raises:
        ValueError: Command is not on the allowlist.
    """
    normalized = " ".join(command.strip().split())
    if normalized not in allowlist:
        raise ValueError(f"Command not allowlisted: {normalized!r}")

    try:
        completed = subprocess.run(
            normalized,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return ShellResult(
            success=False,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + "\n[timeout]",
            returncode=-1,
        )
    except OSError as exc:
        return ShellResult(success=False, stdout="", stderr=str(exc), returncode=-1)

    return ShellResult(
        success=completed.returncode == 0,
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
    )
