"""Command dispatch. UI calls Router.dispatch; execution stays out of widgets."""

from collections.abc import Callable
from dataclasses import dataclass

import psutil

from config.settings import PantheonConfig
from core.fast_path import detect_and_log, format_terminal_output
from core.logger import PantheonLogger

WriteLine = Callable[[str], None]
Prompt = Callable[[], None]
ExitApp = Callable[[], None]
ShowBanner = Callable[[], None]
ClearLog = Callable[[], None]


@dataclass
class DispatchSinks:
    echo_command: Callable[[str], None]
    write_line: WriteLine
    prompt: Prompt
    show_banner: ShowBanner
    clear_log: ClearLog
    exit_app: ExitApp


class Router:
    HELP_TEXT = """[dim]Available commands:[/]

  [bright_cyan]help[/]                 Show commands          [bright_cyan]status[/]               System status
  [bright_cyan]ask <query>[/]          Ask Pantheon            [bright_cyan]memory list[/]          List capsules
  [bright_cyan]task list[/]            List tasks              [bright_cyan]run <command>[/]         Run shell (allowlist)
  [bright_cyan]open <app>[/]           Open application        [bright_cyan]clear[/]                Clear terminal
  [bright_cyan]exit[/]                 Exit Pantheon

[dim]Tier-0 fast path:[/] [bright_cyan]open[/] · [bright_cyan]run <allowlisted>[/] · [bright_cyan]pwd[/]/[bright_cyan]ls[/]/[bright_cyan]git status[/]"""

    def __init__(self, config: PantheonConfig, logger: PantheonLogger) -> None:
        self.config = config
        self.logger = logger

    def dispatch(self, command: str, sinks: DispatchSinks) -> None:
        cmd = command.strip()
        if not cmd:
            return

        sinks.echo_command(cmd)
        lower = cmd.lower()

        # Tier-0: AppleScript + allowlisted shell (plan.json parser tier0)
        fast = detect_and_log(cmd, self.config, self.logger)
        if fast is not None:
            sinks.write_line(format_terminal_output(fast))
            sinks.prompt()
            return

        if lower == "help":
            sinks.write_line(self.HELP_TEXT)
        elif lower == "status":
            sinks.write_line(self._status_text())
            self.logger.info("Status displayed")
        elif lower == "clear":
            sinks.clear_log()
            sinks.show_banner()
        elif lower.startswith("ask "):
            query = cmd[4:].strip()
            self.logger.info(f"Query: {query[:48]}")
            sinks.write_line(
                "\n[bold bright_cyan][Pantheon][/] Processing is not wired yet. Router pending."
            )
            self.logger.info("Query queued (stub)")
        elif lower == "exit":
            sinks.exit_app()
            return
        else:
            self.logger.info(f"Command received: {cmd}")
            sinks.write_line("[dim]→ no tier-0 match; LLM/parser pending[/]")

        sinks.prompt()

    def _status_text(self) -> str:
        vm = psutil.virtual_memory()
        cfg = self.config
        cpu = psutil.cpu_percent(interval=None)
        wal_status = "standby"
        return f"""
[bold bright_cyan]SYSTEM STATUS[/]          [bold bright_cyan]MEMORY STATUS[/]          [bold bright_cyan]PERFORMANCE[/]          [bold bright_cyan]RECOVERY[/]
Mode:      READY            Capsules:     —            Cache Hit:    —          WAL:       {wal_status}
Model:     NONE             Meta:         —            Avg Response: —          Last CP:   —
Context:   —                Graph Nodes:  —            Tokens/sec:   —          Integrity: —
Temperature: —              Embeddings:   —            RAM:          {vm.percent:.0f}%       Status:    [bright_cyan]Healthy[/]
Top-p:     —                Total Size:   —            CPU:          {cpu:.0f}%

[bold bright_cyan]CACHE[/] L1 {cfg.l1_cache_mb}MB · L2 {cfg.l2_cache_mb}MB · L3 {cfg.l3_cache_gb}GB    [bold bright_cyan]FAST PATH[/] tier-0 ON (target 50ms)
"""
