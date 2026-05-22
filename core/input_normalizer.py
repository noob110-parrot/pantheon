"""Shared input normalization for CLI, voice, API, and web surfaces."""

COMMAND_PREFIXES = (
    "help",
    "status",
    "ask ",
    "memory",
    "task",
    "run ",
    "open ",
    "clear",
    "exit",
)


def normalize_input(text: str) -> str:
    """Route natural language to ask; pass explicit commands through unchanged."""
    stripped = text.strip()
    if not stripped:
        return stripped

    lower = stripped.lower()
    if any(lower == prefix.rstrip() or lower.startswith(prefix) for prefix in COMMAND_PREFIXES):
        return stripped
    return f"ask {stripped}"
