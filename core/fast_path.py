"""
Tier-0 fast path detector (plan.json → conflict_resolution.parser_implementation.tier0).

Regex + templates, no LLM, latency target 50ms. Runs before tier1 parser and LLM.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Literal

from config.settings import PantheonConfig
from core.logger import PantheonLogger
from tools.applescript_runner import open_application
from tools.shell_runner import is_allowlisted, run_allowlisted

Route = Literal["applescript", "shell"]
LATENCY_TARGET_MS = 50

_OPEN_RE = re.compile(r"^open\s+(.+)$", re.IGNORECASE)
_RUN_RE = re.compile(r"^run\s+(.+)$", re.IGNORECASE)


@dataclass
class FastPathResult:
    """Outcome of tier-0 detection and execution."""

    route: Route
    command: str
    success: bool
    message: str
    elapsed_ms: float


def detect(command: str, config: PantheonConfig) -> FastPathResult | None:
    """
    Match ``command`` against tier-0 patterns.

    Returns None when the command should fall through to builtins, tier1, or LLM.
    """
    cmd = command.strip()
    if not cmd:
        return None

    allowlist = config.tool_permissions.terminal_allowlist

    match = _OPEN_RE.match(cmd)
    if match:
        return _execute_applescript(match.group(1).strip())

    match = _RUN_RE.match(cmd)
    if match:
        inner = match.group(1).strip()
        if is_allowlisted(inner, allowlist):
            return _execute_shell(inner, allowlist)
        return FastPathResult(
            route="shell",
            command=inner,
            success=False,
            message=f"[red]Denied:[/] '{inner}' is not in terminal_allowlist",
            elapsed_ms=0.0,
        )

    if is_allowlisted(cmd, allowlist):
        return _execute_shell(cmd, allowlist)

    return None


def detect_and_log(command: str, config: PantheonConfig, logger: PantheonLogger) -> FastPathResult | None:
    """Detect, execute, and emit structured + activity logs."""
    result = detect(command, config)
    if result is None:
        return None

    level = "info" if result.success else "error"
    log_msg = (
        f"Fast path {result.route}: {result.command[:48]} "
        f"({result.elapsed_ms:.1f}ms, target {LATENCY_TARGET_MS}ms)"
    )
    if level == "info":
        logger.info(log_msg, success=result.success)
    else:
        logger.error(log_msg)

    if result.elapsed_ms > LATENCY_TARGET_MS:
        logger.info(
            f"Fast path exceeded latency target: {result.elapsed_ms:.1f}ms > {LATENCY_TARGET_MS}ms",
            success=True,
        )

    return result


def format_terminal_output(result: FastPathResult) -> str:
    """Rich markup for the terminal workspace."""
    if result.success:
        body = result.message.strip() or "(no output)"
        return f"[green]✓[/] {result.route}: {body}"
    return f"[yellow]✗[/] {result.message}"


def _execute_applescript(app_name: str) -> FastPathResult:
    start = time.perf_counter()
    outcome = open_application(app_name)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return FastPathResult(
        route="applescript",
        command=f"open {app_name}",
        success=outcome.success,
        message=outcome.message,
        elapsed_ms=elapsed_ms,
    )


def _execute_shell(command: str, allowlist: list[str]) -> FastPathResult:
    start = time.perf_counter()
    try:
        outcome = run_allowlisted(command, allowlist)
    except ValueError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return FastPathResult(
            route="shell",
            command=command,
            success=False,
            message=str(exc),
            elapsed_ms=elapsed_ms,
        )

    elapsed_ms = (time.perf_counter() - start) * 1000
    parts: list[str] = []
    if outcome.stdout.strip():
        parts.append(outcome.stdout.strip())
    if outcome.stderr.strip():
        parts.append(outcome.stderr.strip())
    message = "\n".join(parts) if parts else f"exit {outcome.returncode}"
    return FastPathResult(
        route="shell",
        command=command,
        success=outcome.success,
        message=message,
        elapsed_ms=elapsed_ms,
    )
