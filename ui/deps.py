"""Dependency injection types for the Pantheon UI (no business logic)."""

from dataclasses import dataclass, field

from config.settings import PantheonConfig
from core.logger import PantheonLogger


@dataclass
class DisplayState:
    """Mutable display labels; updated by core subsystems via App, not widgets."""

    model_label: str = "NONE"
    mode_label: str = "READY"
    wal_status: str = "standby"
    recovery_state: str = "healthy"
    active_tab: str = "TERMINAL"


@dataclass
class UIDependencies:
    config: PantheonConfig
    logger: PantheonLogger
    display: DisplayState = field(default_factory=DisplayState)
