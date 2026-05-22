"""Unified logging: structured JSONL on disk + optional UI subscribers."""

from collections.abc import Callable

from config.settings import PantheonConfig
from core.structured_log import emit

UiHandler = Callable[[str, bool], None]


class PantheonLogger:
    def __init__(self, config: PantheonConfig) -> None:
        self.config = config
        self._ui_handlers: list[UiHandler] = []

    def subscribe_ui(self, handler: UiHandler) -> None:
        self._ui_handlers.append(handler)

    def info(self, message: str, *, success: bool = True) -> str | None:
        request_id = emit(self.config, message, success=success)
        for handler in self._ui_handlers:
            handler(message, success)
        return request_id

    def error(self, message: str) -> str | None:
        return self.info(message, success=False)
