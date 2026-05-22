"""Tab panel markup builders (display only; data from subsystems later)."""

from config.settings import PantheonConfig
from ui.art import section_title, stat_row

DEMO_MEMORIES = [
    ("Quantum Computing Basics", "15m ago"),
    ("Understanding Transformer Architecture", "2m ago"),
    ("Vector DB Optimization", "1d ago"),
    ("Project Pantheon Architecture", "1h ago"),
    ("AppleScript Automation Patterns", "3h ago"),
]


def memory_tab_content() -> str:
    rows = "\n".join(
        f"  [#5ce1e6]cap-{i:03d}[/]  {title:<34} [#2a8f9e]{age}[/]"
        for i, (title, age) in enumerate(DEMO_MEMORIES, 1)
    )
    return (
        f"{section_title('MEMORY')}\n\n"
        f"{section_title('STATISTICS')}\n"
        f"{stat_row('Capsules', '—')}  {stat_row('Meta', '—')}\n"
        f"{stat_row('Embeddings', '—')}  {stat_row('Graph', '—')}\n\n"
        f"{section_title('RECENT')}\n"
        f"[#2a8f9e]id       topic                              age[/]\n"
        f"{rows}\n\n"
        f"{section_title('SEARCH')}\n"
        f"[#2a8f9e][FUTURE: memory subsystem search API][/]\n"
        f"[dim]Command: memory search <query>[/]"
    )


def graph_tab_content() -> str:
    return (
        f"{section_title('GRAPH EXPLORER')}\n"
        f"[#2a8f9e][FUTURE: SQLite + NetworkX + FAISS integration][/]\n\n"
        f"[#5ce1e6]           [N-Core][/]\n"
        f"[#5ce1e6]          /   |   \\[/]\n"
        f"[#5ce1e6]      [A-12] [B-07] [C-99][/]\n"
        f"[#5ce1e6]         \\    |    /[/]\n"
        f"[#5ce1e6]          [D-03][/]\n\n"
        f"{section_title('SELECTION')}\n"
        f"{stat_row('Node', '—')}  {stat_row('Edges', '—')}\n"
        f"{stat_row('Relation', '—')}\n\n"
        f"{stat_row('Nodes', '—')}  {stat_row('Total edges', '—')}"
    )


def tasks_tab_content(display_wal: str, display_recovery: str) -> str:
    return (
        f"{section_title('TASK QUEUE')}\n\n"
        f"[bold #5ce1e6]ACTIVE[/]\n"
        f"  [#00ff88]◉[/] [#5ce1e6]—[/]  [#2a8f9e][FUTURE: scheduler][/]\n\n"
        f"[bold #5ce1e6]QUEUED[/]\n"
        f"  [#ffcc00]○[/] [#2a8f9e]—[/]\n\n"
        f"[bold #5ce1e6]COMPLETED[/]\n"
        f"  [#2a8f9e]—[/]\n\n"
        f"{section_title('RECOVERY')}\n"
        f"{stat_row('WAL', display_wal)}\n"
        f"{stat_row('Recovery', display_recovery)}\n"
        f"{stat_row('Scheduler', 'standby')}"
    )


def models_tab_content(config: PantheonConfig, model_label: str, mode_label: str) -> str:
    return (
        f"{section_title('MODEL REGISTRY')}\n\n"
        f"[#00ff88]●[/] [#5ce1e6]{model_label}[/]\n"
        f"    {stat_row('Mode', mode_label)}\n"
        f"    {stat_row('Context', '—')}\n"
        f"    {stat_row('VRAM', '—')}\n"
        f"    {stat_row('Load', 'on-demand' if config.load_on_demand else 'resident')}\n\n"
        f"[#2a8f9e]○[/] [#5ce1e6]Qwen 2.5 3B[/]     [#2a8f9e]utility · unloaded[/]\n"
        f"[#2a8f9e]○[/] [#5ce1e6]DeepSeek 6.7B[/]  [#2a8f9e]coding · unloaded[/]\n\n"
        f"{section_title('POLICY')}\n"
        f"{stat_row('single_active', str(config.single_active_model))}\n"
        f"{stat_row('idle_unload', f'{config.idle_unload_minutes}m')}\n"
        f"[#2a8f9e][FUTURE: ModelManager live metrics][/]"
    )


def system_tab_content(config: PantheonConfig, wal_status: str) -> str:
    return (
        f"{section_title('DIAGNOSTICS')}\n"
        f"{stat_row('Theme', config.theme)}\n"
        f"{stat_row('Logging', 'JSON' if config.structured_logging.json_logs else 'text')}\n"
        f"{stat_row('WAL', wal_status)}\n"
        f"{stat_row('Provenance', 'on' if config.memory_provenance.enabled else 'off')}\n\n"
        f"{section_title('PERFORMANCE')}\n"
        f"[#2a8f9e][FUTURE: per-component latency percentiles][/]\n\n"
        f"{section_title('CONFIDENCE GATES')}\n"
        f"{stat_row('auto_execute', str(config.confidence_thresholds.auto_execute))}\n"
        f"{stat_row('ask_user', str(config.confidence_thresholds.ask_user))}\n"
        f"{stat_row('reject', str(config.confidence_thresholds.reject))}"
    )


def settings_tab_content(config: PantheonConfig) -> str:
    perms = config.tool_permissions
    return (
        f"{section_title('CONFIGURATION')}\n"
        f"{stat_row('theme', config.theme)}\n"
        f"{stat_row('version', config.version)}\n\n"
        f"{section_title('MEMORY')}\n"
        f"{stat_row('provenance', str(config.memory_provenance.enabled))}\n"
        f"{stat_row('ref_count', str(config.reference_counting))}\n"
        f"{stat_row('cow', str(config.copy_on_write))}\n\n"
        f"{section_title('EXECUTION')}\n"
        f"{stat_row('fs_read', str(perms.filesystem.read))}\n"
        f"{stat_row('fs_write', str(perms.filesystem.write))}\n"
        f"{stat_row('network', str(perms.network.outbound))}\n\n"
        f"{section_title('ALLOWLIST')}\n"
        + "\n".join(f"  [#5ce1e6]•[/] [#2a8f9e]{cmd}[/]" for cmd in perms.terminal_allowlist)
    )
