"""Reusable Pantheon TUI widgets (display only — no routing or execution logic)."""

from __future__ import annotations

import os
import platform
import socket
from datetime import datetime
from time import time

import psutil
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import ProgressBar, RichLog, Sparkline, Static, TabbedContent, TabPane

from config.settings import PantheonConfig
from core.logger import PantheonLogger
from ui.art import (
    DRAGON_HEADER_ART,
    DRAGON_SMALL,
    SUBTAGLINE,
    TAGLINE,
    gauge,
    section_title,
    stat_row,
    terminal_banner,
)
from ui.deps import DisplayState, UIDependencies
from ui.tab_panels import (
    DEMO_MEMORIES,
    graph_tab_content,
    memory_tab_content,
    models_tab_content,
    settings_tab_content,
    system_tab_content,
    tasks_tab_content,
)

# ── Header ────────────────────────────────────────────────────────────────────


class PantheonHeader(Horizontal):
    """Top command banner: brand left, status center, model/clock right."""

    def __init__(self, *, deps: UIDependencies) -> None:
        super().__init__(id="top-header")
        self.deps = deps

    def compose(self) -> ComposeResult:
        yield Static(id="header-left")
        yield Static(id="header-center")
        yield Static(id="header-right")

    def on_mount(self) -> None:
        self.refresh_header()
        self.set_interval(1, self.refresh_header)

    def refresh_header(self) -> None:
        cfg = self.deps.config
        display = self.deps.display
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%b %d, %Y").upper()

        vm = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=None)
        disk = psutil.disk_usage("/").percent
        uptime_s = int(time() - psutil.boot_time())
        days, rem = divmod(uptime_s, 86400)
        hours, rem = divmod(rem, 3600)
        mins, _ = divmod(rem, 60)
        uptime = f"{days}d {hours:02d}h {mins:02d}m" if days else f"{hours:02d}h {mins:02d}m"

        threshold = int(cfg.confidence_thresholds.auto_execute * 100)

        self.query_one("#header-left", Static).update(
            f"{DRAGON_SMALL}\n"
            f"[bold #5ce1e6]PANTHEON[/] [bold #00d9ff]v{cfg.version}[/]\n"
            f"[#2a8f9e]ARCHITECTURE HARMONIZED[/]\n"
            f"[#5ce1e6]{TAGLINE}[/]\n"
            f"[#2a8f9e]> {SUBTAGLINE}[/]"
        )

        self.query_one("#header-center", Static).update(
            f"[#00ff88]● SYSTEM ONLINE[/]  [#2a8f9e]UPTIME {uptime}[/]\n"
            f"[#5ce1e6]CONFIDENCE GATE[/]  [#00ff88]█[/] {threshold}%  "
            f"[#2a8f9e]threshold {threshold}%[/]\n"
            f"[#5ce1e6]RESOURCES[/]  CPU {cpu:4.1f}%  RAM {vm.percent:4.1f}%  "
            f"DISK {disk:4.1f}%  [#2a8f9e]TAB {display.active_tab}[/]"
        )

        self.query_one("#header-right", Static).update(
            f"{DRAGON_HEADER_ART}\n"
            f"[#5ce1e6]MODEL[/]\n[bold #00d9ff]{display.model_label}[/]\n\n"
            f"[#5ce1e6]MODE[/]\n[bold]{display.mode_label}[/]\n\n"
            f"[bold #00d9ff]{time_str}[/]\n[#2a8f9e]{date_str}[/]"
        )


# ── Left column ─────────────────────────────────────────────────────────────


class SystemOverviewPanel(Static):
    def __init__(self, *, deps: UIDependencies) -> None:
        super().__init__(classes="panel-box")
        self.deps = deps
        self._cpu_history: list[float] = []

    def compose(self) -> ComposeResult:
        yield Static(f"{section_title('SYSTEM OVERVIEW')}\n[#2a8f9e]Loading…[/]", id="sys-text")
        yield Static("[#2a8f9e]CPU USAGE[/]", classes="gauge-label")
        yield ProgressBar(total=100, show_eta=False, id="cpu-bar")
        yield Sparkline(data=[0.0], id="cpu-spark")
        yield Static("[#2a8f9e]MEMORY[/]", classes="gauge-label")
        yield ProgressBar(total=100, show_eta=False, id="ram-bar")
        yield Static("[#2a8f9e]SWAP[/]", classes="gauge-label")
        yield ProgressBar(total=100, show_eta=False, id="swap-bar")
        yield Static("[#2a8f9e]DISK[/]", classes="gauge-label")
        yield ProgressBar(total=100, show_eta=False, id="disk-bar")

    def on_mount(self) -> None:
        psutil.cpu_percent(interval=None)
        self.refresh_stats()
        self.set_interval(2, self.refresh_stats)

    def refresh_stats(self) -> None:
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu = psutil.cpu_percent(interval=None)
        try:
            swap = psutil.swap_memory()
            swap_pct = swap.percent if swap.total else 0.0
        except (PermissionError, OSError):
            swap_pct = 0.0

        uptime_s = int(time() - psutil.boot_time())
        hours, rem = divmod(uptime_s, 3600)
        mins, secs = divmod(rem, 60)
        host = socket.gethostname().split(".")[0]
        user = os.getenv("USER", "user")
        release = platform.mac_ver()[0] or platform.release()
        os_label = f"{platform.system()} {release}".strip()

        self._cpu_history = (self._cpu_history + [cpu])[-32:]
        self.query_one("#cpu-bar", ProgressBar).update(progress=cpu)
        self.query_one("#ram-bar", ProgressBar).update(progress=vm.percent)
        self.query_one("#swap-bar", ProgressBar).update(progress=swap_pct)
        self.query_one("#disk-bar", ProgressBar).update(progress=disk.percent)
        self.query_one("#cpu-spark", Sparkline).data = self._cpu_history

        self.query_one("#sys-text", Static).update(
            f"{section_title('SYSTEM OVERVIEW')}\n"
            f"{stat_row('Uptime', f'{hours:02d}:{mins:02d}:{secs:02d}')}\n"
            f"{stat_row('OS', os_label)}\n"
            f"{stat_row('Host', host)}\n"
            f"{stat_row('User', user)}"
        )


class MemoryStatsPanel(Static):
    def __init__(self, *, deps: UIDependencies) -> None:
        super().__init__(classes="panel-box")
        self.deps = deps

    def on_mount(self) -> None:
        self.update(
            f"{section_title('PANTHEON MEMORY')}\n"
            f"{stat_row('Capsules', '—')}\n"
            f"{stat_row('Meta Capsules', '—')}\n"
            f"{stat_row('Graph Nodes', '—')}\n"
            f"{stat_row('Graph Edges', '—')}\n"
            f"{stat_row('Embeddings', '—')}\n"
            f"[#2a8f9e][FUTURE: memory subsystem metrics][/]"
        )


class CacheStatusPanel(Static):
    def __init__(self, *, config: PantheonConfig) -> None:
        super().__init__(classes="panel-box")
        self.config = config

    def compose(self) -> ComposeResult:
        yield Static(id="cache-text")
        yield Static(f"[#2a8f9e]L1 ({self.config.l1_cache_mb}MB)[/]", classes="gauge-label")
        yield ProgressBar(total=100, show_eta=False, id="l1-bar")
        yield Static(f"[#2a8f9e]L2 ({self.config.l2_cache_mb}MB)[/]", classes="gauge-label")
        yield ProgressBar(total=100, show_eta=False, id="l2-bar")
        yield Static(f"[#2a8f9e]L3 ({self.config.l3_cache_gb}GB)[/]", classes="gauge-label")
        yield ProgressBar(total=100, show_eta=False, id="l3-bar")

    def on_mount(self) -> None:
        self.query_one("#cache-text", Static).update(
            f"{section_title('CACHE STATUS')}\n{stat_row('Hit Rate', '—')}"
        )
        for bar_id in ("l1-bar", "l2-bar", "l3-bar"):
            self.query_one(f"#{bar_id}", ProgressBar).update(progress=0.0)


class TasksWalPanel(Static):
    def __init__(self, *, display_state: DisplayState) -> None:
        super().__init__(classes="panel-box")
        self.display_state = display_state

    def render(self) -> str:
        return (
            f"{section_title('TASKS / WAL')}\n"
            f"{stat_row('Active', '0')}\n"
            f"{stat_row('Queued', '0')}\n"
            f"{stat_row('Completed', '0')}\n"
            f"{stat_row('WAL', self.display_state.wal_status)}\n"
            f"{stat_row('Last CP', '—')}\n"
            f"{stat_row('Recovery', self.display_state.recovery_state)}"
        )


class LeftRail(Vertical):
    def __init__(self, *, deps: UIDependencies) -> None:
        super().__init__(id="left-rail")
        self.deps = deps

    def compose(self) -> ComposeResult:
        yield SystemOverviewPanel(deps=self.deps)
        yield MemoryStatsPanel(deps=self.deps)
        yield CacheStatusPanel(config=self.deps.config)
        yield TasksWalPanel(display_state=self.deps.display)


# ── Center: workspace tabs ────────────────────────────────────────────────────


class TerminalWorkspace(Vertical):
    """Tabbed workspace; terminal view exposes write API for Router sinks."""

    def __init__(self, *, deps: UIDependencies) -> None:
        super().__init__(id="center-workspace")
        self.deps = deps
        self.terminal_log: RichLog | None = None
        self.host = socket.gethostname().split(".")[0]

    def compose(self) -> ComposeResult:
        cfg = self.deps.config
        display = self.deps.display
        with TabbedContent(id="workspace-tabs", initial="tab-terminal"):
            with TabPane("TERMINAL", id="tab-terminal"):
                self.terminal_log = RichLog(
                    id="terminal-log", highlight=True, markup=True, wrap=True
                )
                yield self.terminal_log
            with TabPane("MEMORY", id="tab-memory"):
                yield Static(memory_tab_content(), classes="tab-panel")
            with TabPane("GRAPH", id="tab-graph"):
                yield Static(graph_tab_content(), classes="tab-panel")
            with TabPane("TASKS", id="tab-tasks"):
                yield Static(
                    tasks_tab_content(display.wal_status, display.recovery_state),
                    classes="tab-panel",
                )
            with TabPane("MODELS", id="tab-models"):
                yield Static(
                    models_tab_content(cfg, display.model_label, display.mode_label),
                    classes="tab-panel",
                )
            with TabPane("SYSTEM", id="tab-system"):
                yield Static(system_tab_content(cfg, display.wal_status), classes="tab-panel")
            with TabPane("SETTINGS", id="tab-settings"):
                yield Static(settings_tab_content(cfg), classes="tab-panel")

    def on_mount(self) -> None:
        assert self.terminal_log is not None
        self.write_line(terminal_banner(self.host))
        self.write_line("")
        self.write_line("[#2a8f9e]Commands: help · status · ask · memory · open · run · clear · exit[/]")
        self.prompt()

    def prompt(self) -> None:
        self.write_line(
            f"\n[bold #5ce1e6]pantheon@{self.host}[/] [#2a8f9e]~[/] % ", end=""
        )

    def write_line(self, text: str, *, end: str = "\n") -> None:
        if self.terminal_log:
            self.terminal_log.write(text + end)

    def echo_command(self, command: str) -> None:
        self.write_line(f"[bold #5ce1e6]pantheon@{self.host}[/] [#2a8f9e]~[/] % {command}")

    def show_banner(self) -> None:
        self.write_line(terminal_banner(self.host))

    def clear_log(self) -> None:
        if self.terminal_log:
            self.terminal_log.clear()


# ── Right column ──────────────────────────────────────────────────────────────


class ActivityFeed(Static):
    def __init__(self, *, logger: PantheonLogger) -> None:
        super().__init__(id="activity-feed", classes="panel-box")
        self.logger = logger
        self._entries: list[tuple[str, str, str]] = []

    def on_mount(self) -> None:
        self.logger.subscribe_ui(self._on_log)

    def render(self) -> str:
        if not self._entries:
            return f"{section_title('ACTIVITY FEED')}\n[#2a8f9e]Awaiting events…[/]"
        lines = [f"{dot} {ts}  {msg}" for dot, ts, msg in self._entries[-10:]]
        return f"{section_title('ACTIVITY FEED')}\n" + "\n".join(lines)

    def _on_log(self, message: str, success: bool) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        dot = "[#00ff88]●[/]" if success else "[#ff4477]●[/]"
        self._entries.append((dot, ts, message))
        self.refresh()

    def add_log(self, message: str, *, success: bool = True) -> None:
        if success:
            self.logger.info(message, success=True)
        else:
            self.logger.error(message)


class RecentMemoriesPanel(Static):
    def __init__(self, *args, **kwargs) -> None:
        rows = "\n".join(
            f"[#5ce1e6]•[/] {title}\n  [#2a8f9e]{age}[/]" for title, age in DEMO_MEMORIES[:5]
        )
        super().__init__(f"{section_title('RECENT MEMORIES')}\n{rows}", *args, **kwargs)


class SystemAlertsPanel(Static):
    def __init__(self, *, display_state: DisplayState, **kwargs) -> None:
        disk = psutil.disk_usage("/")
        free_pct = 100 - disk.percent
        alerts = [
            "[#00ff88]✓[/] All systems operational",
            "[#00ff88]✓[/] Config loaded",
            "[#00ff88]✓[/] Dragon UI online",
        ]
        if free_pct < 30:
            alerts.append(f"[#ffcc00]![/] Low disk space ({free_pct:.0f}% left)")
        if display_state.model_label == "NONE":
            alerts.append(f"[#ff4477]![/] Model standby — no active inference")
        super().__init__(f"{section_title('SYSTEM ALERTS')}\n" + "\n".join(alerts), **kwargs)


class NetworkPanel(Static):
    def __init__(self, *args, **kwargs) -> None:
        hostname = socket.gethostname()
        super().__init__(
            f"{section_title('NETWORK STATUS')}\n"
            f"[bold #00ff88]● CONNECTED[/]  [#2a8f9e]local-only[/]\n"
            f"[#2a8f9e]    ◇───◇───◇[/]\n"
            f"[#2a8f9e]     \\     /[/]\n"
            f"[#2a8f9e]      ◇───◇[/]\n"
            f"{stat_row('Host', hostname)}\n"
            f"{stat_row('Latency', '—')}\n"
            f"[#2a8f9e]No external API required.[/]",
            *args,
            **kwargs,
        )


class RightRail(Vertical):
    def __init__(self, *, deps: UIDependencies) -> None:
        super().__init__(id="right-rail")
        self.deps = deps

    def compose(self) -> ComposeResult:
        self.feed = ActivityFeed(logger=self.deps.logger)
        yield self.feed
        yield RecentMemoriesPanel(classes="panel-box")
        yield SystemAlertsPanel(display_state=self.deps.display, classes="panel-box")
        yield NetworkPanel(classes="panel-box", id="network-panel")


# ── Footer ────────────────────────────────────────────────────────────────────


class ShortcutFooter(Horizontal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(id="shortcut-footer", *args, **kwargs)

    def compose(self) -> ComposeResult:
        yield Static(id="footer-shortcuts")
        yield Static(id="footer-tagline")

    def on_mount(self) -> None:
        self.query_one("#footer-shortcuts", Static).update(
            "[#2a8f9e]TAB[/] Complete  "
            "[#5ce1e6]↑↓[/] History  "
            "[#5ce1e6]CTRL+K[/] Clear  "
            "[#5ce1e6]CTRL+S[/] Save  "
            "[#5ce1e6]CTRL+R[/] Search  "
            "[#5ce1e6]?[/] Help  "
            "[#5ce1e6]ESC[/] Exit"
        )
        self.query_one("#footer-tagline", Static).update(
            "[#2a8f9e]Built for speed. Designed for power.[/]  🐉"
        )
