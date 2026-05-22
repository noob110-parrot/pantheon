"""ASCII art and panel chrome for the Pantheon TUI."""

DRAGON_SMALL = (
    "[#5ce1e6]   /\\__/\\\n"
    "  ( ◉  ◉ )\n"
    "   /    \\[/]"
)

DRAGON_HEADER_ART = (
    "[bold #00d9ff]     __---__\n"
    "    /       \\\n"
    "   |  ◉   ◉  |\n"
    "    \\  ▽  /\n"
    "     --|||--[/]"
)

DRAGON_BANNER = (
    "[#5ce1e6]       /\\  /\\\n"
    "      /  \\/  \\\n"
    "     | ( )( ) |\n"
    "      \\  /\\  /\n"
    "       \\/  \\/[/]"
)

TAGLINE = "Intelligence • Memory • Execution"
SUBTAGLINE = "Local First • Private Always"

SECTION = "━" * 24


def section_title(title: str) -> str:
    return f"[bold #5ce1e6]{title}[/]\n[#2a8f9e]{SECTION}[/]"


def stat_row(label: str, value: str, *, width: int = 11) -> str:
    return f"[#2a8f9e]{label:<{width}}[/] [#5ce1e6]{value}[/]"


def gauge(label: str, pct: float, detail: str = "", *, width: int = 18) -> str:
    filled = int(width * min(max(pct, 0), 100) / 100)
    track = "█" * filled + "░" * (width - filled)
    extra = f"  [#2a8f9e]{detail}[/]" if detail else ""
    return f"[#2a8f9e]{label:<6}[/] [#5ce1e6]{track}[/] {pct:5.1f}%{extra}"


def terminal_banner(host: str) -> str:
    return (
        f"[bold #2a8f9e]╔══════════════════════════════════════════════════════════════╗[/]\n"
        f"[bold #2a8f9e]║[/] [#5ce1e6]PANTHEON[/]  {DRAGON_BANNER}                         [bold #2a8f9e]║[/]\n"
        f"[bold #2a8f9e]║[/] [bold #00ff88]DRAGON CORE ONLINE[/]                                      [bold #2a8f9e]║[/]\n"
        f"[bold #2a8f9e]║[/]                                                              [bold #2a8f9e]║[/]\n"
        f"[bold #2a8f9e]║[/]  [bold white]Intelligence.[/]                                           [bold #2a8f9e]║[/]\n"
        f"[bold #2a8f9e]║[/]  [bold white]Memory.[/]                                                 [bold #2a8f9e]║[/]\n"
        f"[bold #2a8f9e]║[/]  [bold white]Execution.[/]                                            [bold #2a8f9e]║[/]\n"
        f"[bold #2a8f9e]║[/]                                                              [bold #2a8f9e]║[/]\n"
        f"[bold #2a8f9e]║[/]  [#2a8f9e]> {TAGLINE}[/]                           [bold #2a8f9e]║[/]\n"
        f"[bold #2a8f9e]║[/]  [#2a8f9e]> {SUBTAGLINE}[/]                              [bold #2a8f9e]║[/]\n"
        f"[bold #2a8f9e]╚══════════════════════════════════════════════════════════════╝[/]\n"
        f"[#2a8f9e]Host: [#5ce1e6]{host}[/]  ·  [#2a8f9e]Pipeline: Input → Normalizer → Router → Executor[/]"
    )
