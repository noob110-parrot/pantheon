import json
from pathlib import Path

from pydantic import BaseModel


class StructuredLogging(BaseModel):
    enabled: bool
    json_logs: bool


class RequestTracking(BaseModel):
    enabled: bool


class ConfidenceThresholds(BaseModel):
    auto_execute: float
    ask_user: float
    reject: float


class MemoryProvenance(BaseModel):
    enabled: bool


class FilesystemPermissions(BaseModel):
    read: bool
    write: bool


class NetworkPermissions(BaseModel):
    outbound: bool


class ToolPermissions(BaseModel):
    filesystem: FilesystemPermissions
    terminal_allowlist: list[str]
    network: NetworkPermissions


class PantheonConfig(BaseModel):
    project_name: str
    version: str
    theme: str
    single_active_model: bool
    resident_small_model: bool
    load_on_demand: bool
    idle_unload_minutes: int
    l1_cache_mb: int
    l2_cache_mb: int
    l3_cache_gb: int
    structured_logging: StructuredLogging
    request_tracking: RequestTracking
    confidence_thresholds: ConfidenceThresholds
    memory_provenance: MemoryProvenance
    tool_permissions: ToolPermissions
    future_distributed_support: bool
    two_phase_commit: bool
    reference_counting: bool
    copy_on_write: bool
    zero_copy_mmap: bool


def load_config(path: Path | None = None) -> PantheonConfig:
    config_path = path or Path(__file__).parent / "config.json"
    data = json.loads(config_path.read_text())
    return PantheonConfig.model_validate(data)
