import path_setup  # noqa: F401

from config.settings import load_config
from ui.terminal_ui import run


def main() -> None:
    run(load_config())


if __name__ == "__main__":
    main()
