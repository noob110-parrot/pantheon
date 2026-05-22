from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static


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
                yield Static(
"""
🐉 PANTHEON CORE

CPU: --
RAM: --
CACHE: --
MODEL: NONE

STATUS:
ONLINE
"""
                )

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
