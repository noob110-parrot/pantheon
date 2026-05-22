"""
Pantheon TUI — composition layer only.

Pipeline (owned by core/, not UI):
  Input → Input Normalizer → Router → Planner → Executor
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Static

from config.settings import PantheonConfig, load_config
from core.input_normalizer import normalize_input
from core.logger import PantheonLogger
from core.router import DispatchSinks, Router
from ui.deps import DisplayState, UIDependencies
from ui.panels import (
    LeftRail,
    PantheonHeader,
    RightRail,
    ShortcutFooter,
    TerminalWorkspace,
)

THEME_PATH = Path(__file__).parent / "theme.tcss"


class PantheonUI(App):
    """Composes widgets and dispatches input to Router (no business logic here)."""

    TITLE = "Pantheon"
    CSS_PATH = THEME_PATH

    BINDINGS = [
        ("escape", "quit", "Exit"),
        ("ctrl+k", "clear_terminal", "Clear"),
        ("question_mark", "show_help", "Help"),
    ]

    def __init__(self, config: PantheonConfig) -> None:
        super().__init__()
        self.deps = UIDependencies(
            config=config,
            logger=PantheonLogger(config),
            display=DisplayState(
                model_label="Qwen 2.5 7B (standby)",
                mode_label="REASONING",
            ),
        )
        self.router = Router(config, self.deps.logger)

    def compose(self) -> ComposeResult:
        yield PantheonHeader(deps=self.deps)

        with Horizontal(id="main-row"):
            yield LeftRail(deps=self.deps)

            with Vertical(id="center-rail"):
                self.workspace = TerminalWorkspace(deps=self.deps)
                yield self.workspace

            self.right_rail = RightRail(deps=self.deps)
            yield self.right_rail

        with Horizontal(id="command-row"):
            yield Static("🐉", id="command-prompt")
            yield Input(placeholder="Ask Pantheon anything...", id="command-input")
            yield Static("ENTER", id="enter-hint")

        yield ShortcutFooter()

    @property
    def feed(self):
        return self.right_rail.feed

    def on_mount(self) -> None:
        cfg = self.deps.config
        self.feed.add_log(f"{cfg.project_name} v{cfg.version} online")
        self.feed.add_log("Config loaded")
        self.feed.add_log("Memory subsystem standby")
        self.feed.add_log("Dragon command interface ready")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "command-input":
            return

        raw = event.value.strip()
        event.input.value = ""
        if not raw:
            return

        self.deps.display.active_tab = "TERMINAL"
        self.router.dispatch(normalize_input(raw), self._dispatch_sinks())

    def _dispatch_sinks(self) -> DispatchSinks:
        ws = self.workspace
        return DispatchSinks(
            echo_command=ws.echo_command,
            write_line=ws.write_line,
            prompt=ws.prompt,
            show_banner=ws.show_banner,
            clear_log=ws.clear_log,
            exit_app=self.exit,
        )

    def action_clear_terminal(self) -> None:
        self.router.dispatch("clear", self._dispatch_sinks())

    def action_show_help(self) -> None:
        self.router.dispatch("help", self._dispatch_sinks())


def run(config: PantheonConfig | None = None) -> None:
    PantheonUI(config or load_config()).run()


if __name__ == "__main__":
    run()
