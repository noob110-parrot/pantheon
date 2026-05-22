"""
Pantheon model lifecycle manager.

Enforces single active inference model, on-demand loading, idle unload, and RAM
budget checks. Inference backends are pluggable later; this module owns policy.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

import psutil

from config.settings import PantheonConfig

Role = Literal["reasoning", "coding", "utility"]
ModelStateName = Literal["unloaded", "loading", "ready", "active", "unloading"]


class ModelLoadError(Exception):
    """Raised when a model cannot be loaded within policy or RAM limits."""


class RamBudgetExceeded(ModelLoadError):
    """Raised when activating a model would exceed the configured RAM ceiling."""


@dataclass(frozen=True)
class ModelSpec:
    """Catalog entry for a replaceable model by role."""

    id: str
    display_name: str
    role: Role
    estimated_ram_mb: int
    tier: Literal["resident_small", "on_demand"]


# Catalog aligned with project constraints (MacBook Air 16GB).
MODEL_CATALOG: tuple[ModelSpec, ...] = (
    ModelSpec("phi-3-mini", "Phi-3 Mini 3.8B", "utility", 512, "resident_small"),
    ModelSpec("qwen-3b", "Qwen 2.5 3B", "utility", 768, "resident_small"),
    ModelSpec("qwen-7b", "Qwen 2.5 7B", "reasoning", 5200, "on_demand"),
    ModelSpec("deepseek-6.7b", "DeepSeek 6.7B", "coding", 4800, "on_demand"),
)


@dataclass
class ModelRuntime:
    spec: ModelSpec
    state: ModelStateName = "unloaded"
    last_used_monotonic: float = field(default_factory=time.monotonic)
    loaded_at_monotonic: float | None = None


def manage_model_activation(
    manager: ModelManager,
    role: Role,
    *,
    force: bool = False,
) -> ModelRuntime:
    """
    Activate the best catalog model for ``role`` under Pantheon RAM policy.

    This is the single entry point for model lifecycle changes during Phase 1.
    Loads on demand, unloads competing active models, and updates runtime state.
    Does not run inference — only prepares the active model slot.

    Args:
        manager: Initialized ModelManager bound to config and catalog.
        role: Target cognitive role (reasoning, coding, utility).
        force: If True, skip idle unload sweep before load (use sparingly).

    Returns:
        ModelRuntime for the activated model in ``ready`` or ``active`` state.

    Raises:
        ModelLoadError: Unknown role or catalog miss.
        RamBudgetExceeded: Activation would exceed idle/active RAM ceilings.
    """
    if role not in ("reasoning", "coding", "utility"):
        raise ModelLoadError(f"Unknown role: {role!r}")

    if not force:
        manager.unload_idle()

    spec = manager.resolve_spec_for_role(role)
    runtime = manager.runtimes[spec.id]

    projected = manager.projected_ram_mb_if_active(spec)
    if projected > manager.active_ram_ceiling_mb:
        raise RamBudgetExceeded(
            f"Cannot activate {spec.display_name}: projected {projected}MB "
            f"> active ceiling {manager.active_ram_ceiling_mb}MB"
        )

    if manager.config.single_active_model:
        manager._deactivate_others(except_id=spec.id)

    if runtime.state in ("unloaded", "unloading"):
        runtime.state = "loading"
        # Phase 2: call llama.cpp / mlx loader here.
        runtime.state = "ready"
        runtime.loaded_at_monotonic = time.monotonic()

    runtime.state = "active"
    runtime.last_used_monotonic = time.monotonic()
    manager._active_id = spec.id
    return runtime


class ModelManager:
    """
    Tracks loaded models and enforces plan.json model_management_v2 policy.

    RAM ceilings (defaults, overridable via config in Phase 2):
      - idle_budget_mb: 4096
      - active_budget_mb: 12288
      - hard_limit_mb: 16384
    """

    def __init__(
        self,
        config: PantheonConfig,
        *,
        idle_ram_ceiling_mb: int = 4096,
        active_ram_ceiling_mb: int = 12288,
        hard_ram_limit_mb: int = 16384,
        max_loaded_models: int = 2,
    ) -> None:
        self.config = config
        self.idle_ram_ceiling_mb = idle_ram_ceiling_mb
        self.active_ram_ceiling_mb = active_ram_ceiling_mb
        self.hard_ram_limit_mb = hard_ram_limit_mb
        self.max_loaded_models = max_loaded_models
        self.idle_unload_seconds = config.idle_unload_minutes * 60
        self.runtimes: dict[str, ModelRuntime] = {
            spec.id: ModelRuntime(spec=spec) for spec in MODEL_CATALOG
        }
        self._active_id: str | None = None

    def resolve_spec_for_role(self, role: Role) -> ModelSpec:
        """Pick the default on-demand (or resident) model for a role."""
        matches = [s for s in MODEL_CATALOG if s.role == role]
        if not matches:
            raise ModelLoadError(f"No catalog model for role {role!r}")

        if self.config.resident_small_model and role == "utility":
            for spec in matches:
                if spec.tier == "resident_small":
                    return spec

        on_demand = [s for s in matches if s.tier == "on_demand"]
        return on_demand[0] if on_demand else matches[0]

    def projected_ram_mb_if_active(self, spec: ModelSpec) -> int:
        """Estimate total RAM if ``spec`` becomes active (loaded + system)."""
        loaded_mb = sum(
            r.spec.estimated_ram_mb
            for r in self.runtimes.values()
            if r.state in ("ready", "active", "loading") and r.spec.id != spec.id
        )
        system_mb = int(psutil.virtual_memory().used / (1024 * 1024))
        return loaded_mb + spec.estimated_ram_mb + max(system_mb // 4, 512)

    def unload_idle(self) -> list[str]:
        """Unload models idle longer than config.idle_unload_minutes."""
        now = time.monotonic()
        unloaded: list[str] = []
        loaded = [
            r
            for r in self.runtimes.values()
            if r.state in ("ready", "active") and r.spec.id != self._active_id
        ]
        loaded.sort(key=lambda r: r.last_used_monotonic)

        while len(loaded) >= self.max_loaded_models:
            victim = loaded.pop(0)
            if now - victim.last_used_monotonic >= self.idle_unload_seconds:
                victim.state = "unloaded"
                victim.loaded_at_monotonic = None
                unloaded.append(victim.spec.id)

        for runtime in self.runtimes.values():
            if runtime.spec.id == self._active_id:
                continue
            if runtime.state not in ("ready", "active"):
                continue
            if now - runtime.last_used_monotonic < self.idle_unload_seconds:
                continue
            runtime.state = "unloaded"
            runtime.loaded_at_monotonic = None
            unloaded.append(runtime.spec.id)

        return unloaded

    def active_runtime(self) -> ModelRuntime | None:
        if self._active_id is None:
            return None
        return self.runtimes.get(self._active_id)

    def status_summary(self) -> dict[str, str]:
        """Lightweight status for UI / router (no psutil side effects)."""
        active = self.active_runtime()
        return {
            "active_model": active.spec.display_name if active else "NONE",
            "active_role": active.spec.role if active else "—",
            "active_state": active.state if active else "unloaded",
            "loaded_count": str(
                sum(1 for r in self.runtimes.values() if r.state in ("ready", "active", "loading"))
            ),
        }

    def _deactivate_others(self, *, except_id: str) -> None:
        for runtime in self.runtimes.values():
            if runtime.spec.id == except_id:
                continue
            if runtime.state == "active":
                runtime.state = "ready"
            if runtime.state in ("ready", "loading") and self.config.load_on_demand:
                if self._count_loaded() > self.max_loaded_models:
                    runtime.state = "unloaded"
                    runtime.loaded_at_monotonic = None

    def _count_loaded(self) -> int:
        return sum(
            1 for r in self.runtimes.values() if r.state in ("ready", "active", "loading")
        )
