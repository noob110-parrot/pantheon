from textual.app import App
from textual.widgets import Header, Footer


class PantheonUI(App):

    def compose(self):
        yield Header()
        yield Footer()


if __name__ == "__main__":
    PantheonUI().run()
