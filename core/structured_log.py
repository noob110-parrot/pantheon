"""Append-only JSONL logs. No-op when structured_logging is disabled."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config.settings import PantheonConfig

LOG_DIR = Path("pantheon_data/logs")


def emit(
    config: PantheonConfig,
    message: str,
    *,
    success: bool = True,
    request_id: str | None = None,
) -> str | None:
    """Write one log entry. Returns request_id when tracking is enabled."""
    if not config.structured_logging.enabled:
        return None

    rid = request_id
    if rid is None and config.request_tracking.enabled:
        rid = str(uuid.uuid4())

    entry: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": message,
        "success": success,
    }
    if rid:
        entry["request_id"] = rid

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")

    return rid
