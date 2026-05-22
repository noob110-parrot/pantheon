from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static
import psutil


class MetricsPanel(Static):

    def on_mount(self):
        self.set_interval(1, self.update_metrics)

    def update_metrics(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        self.update(
f"""
🐉 PANTHEON CORE

CPU: {cpu:.1f}%
RAM: {ram:.1f}%

CACHE: --
MODEL: NONE

STATUS:
ONLINE
"""
        )


class PantheonUI(App):

    CSS = """
    Screen {
        layout: vertical;
    }

    #main {
        height: 1fr;
    }

    #left {
        width: 30%;
        border: solid green;
    }

    #right {
        width: 70%;
        border: solid cyan;
    }

    #command {
        height: 3;
        border: solid yellow;
    }
    """

    def compose(self) -> ComposeResult:

        yield Header()

        with Horizontal(id="main"):

            with Vertical(id="left"):
                yield MetricsPanel()

            with Vertical(id="right"):
                yield Static(
"""
Activity Feed

Pantheon initialized.
Waiting for command...
"""
                )

        yield Static("> ", id="command")

        yield Footer()


if __name__ == "__main__":
    PantheonUI().run()
