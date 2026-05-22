"""Terminal-native Pantheon Core visualization panel."""

from __future__ import annotations

import math
from time import monotonic

from textual.widgets import Static

from core.logger import PantheonLogger
from ui.art import section_title, stat_row


class PantheonCorePanel(Static):
    """Animated TRON-style reactor and neural mesh for the right sidebar."""

    NODE_LABELS = ["MEM", "CDX", "RSH", "KRN", "FIN", "TLS", "MDL", "VDB"]
    EDGE_INDEXES = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 0),
        (0, 4),
        (2, 6),
        (1, 5),
        (3, 7),
    ]

    def __init__(self, *, logger: PantheonLogger, **kwargs) -> None:
        super().__init__(**kwargs)
        self.logger = logger
        self._tick = 0
        self._mode = "idle"
        self._mode_until = 0.0
        self._active_node = 0
        self._fallback_level = 0

    def on_mount(self) -> None:
        self.logger.subscribe_ui(self._on_log)
        self._render_frame()
        self.set_interval(0.16, self._render_frame)

    def _on_log(self, message: str, success: bool) -> None:
        lower = message.lower()
        now = monotonic()

        if any(t in lower for t in ("memory", "capsule", "vector", "embedding")):
            self._mode = "memory_access"
            self._mode_until = now + 2.4
            return

        if any(t in lower for t in ("task", "tool", "run ", "open ", "query", "command")):
            self._mode = "tool_execution"
            self._active_node = (self._active_node + 1) % len(self.NODE_LABELS)
            self._mode_until = now + 2.4
            return

        if any(t in lower for t in ("ask", "model", "reason", "status", "thinking")):
            self._mode = "thinking"
            self._mode_until = now + 1.8
            return

        if not success:
            self._mode = "thinking"
            self._mode_until = now + 1.6

    def _render_frame(self) -> None:
        self._tick += 1
        if self._mode != "idle" and monotonic() > self._mode_until:
            self._mode = "idle"
        try:
            if self._fallback_level == 0:
                body = self._frame_text()
            elif self._fallback_level == 1:
                body = self._fallback_static_reactor()
            elif self._fallback_level == 2:
                body = self._fallback_neural_only()
            elif self._fallback_level == 3:
                body = self._fallback_unicode_panel()
            else:
                body = self._fallback_disabled()
            self.update(body)
        except Exception:
            self._fallback_level = min(4, self._fallback_level + 1)
            if self._fallback_level == 1:
                self.update(self._fallback_static_reactor())
            elif self._fallback_level == 2:
                self.update(self._fallback_neural_only())
            elif self._fallback_level == 3:
                self.update(self._fallback_unicode_panel())
            else:
                self.update(self._fallback_disabled())

    def _frame_text(self) -> str:
        width = max(28, min(46, (self.size.width or 38) - 2))
        height = 11
        grid: list[list[str]] = [[" " for _ in range(width)] for _ in range(height)]
        color: list[list[str | None]] = [[None for _ in range(width)] for _ in range(height)]

        def put(x: int, y: int, ch: str, c: str | None = None) -> None:
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = ch
                color[y][x] = c

        def line(x0: int, y0: int, x1: int, y1: int, ch: str, c: str) -> None:
            steps = max(abs(x1 - x0), abs(y1 - y0))
            if steps <= 0:
                put(x0, y0, ch, c)
                return
            for i in range(steps + 1):
                t = i / steps
                x = round(x0 + (x1 - x0) * t)
                y = round(y0 + (y1 - y0) * t)
                if grid[y][x] == " ":
                    put(x, y, ch, c)

        cx = width // 2
        cy = height // 2
        pulse = 1.0 + math.sin(self._tick * 0.25) * 0.2

        ring_data = [(2.0, 0.18), (3.5, -0.13), (5.0, 0.09)]
        ring_chars = ("·", "◦", "◌")
        for idx, (r, speed) in enumerate(ring_data):
            phase = self._tick * speed
            for s in range(20):
                a = (2 * math.pi * s / 20.0) + phase
                x = int(round(cx + math.cos(a) * (r * 1.7)))
                y = int(round(cy + math.sin(a) * r))
                ch = "◉" if s % 10 == 0 else ring_chars[idx]
                put(x, y, ch, "#00aaff")

        core_symbol = "⬢" if pulse >= 1.0 else "◈"
        put(cx, cy, core_symbol, "#00ffff")
        put(cx - 1, cy, "●", "#00ffff")
        put(cx + 1, cy, "●", "#00ffff")

        node_radius = max(4, min(6, width // 8))
        node_positions: list[tuple[int, int]] = []
        for i in range(len(self.NODE_LABELS)):
            a = (2 * math.pi * i / len(self.NODE_LABELS)) - math.pi / 2
            x = int(round(cx + math.cos(a) * (node_radius * 2.4)))
            y = int(round(cy + math.sin(a) * node_radius))
            node_positions.append((x, y))

        for a_idx, b_idx in self.EDGE_INDEXES:
            x0, y0 = node_positions[a_idx]
            x1, y1 = node_positions[b_idx]
            line(x0, y0, x1, y1, "┄", "#2a8f9e")

        for i, (x, y) in enumerate(node_positions):
            node_char = "●"
            node_color = "#5ce1e6"
            if self._mode == "memory_access" and i in (0, 7):
                node_char = "◈"
                node_color = "#ffffff" if self._tick % 2 else "#00ffff"
            if self._mode == "tool_execution" and i == self._active_node:
                node_char = "▣"
                node_color = "#ffffff"
            put(x, y, node_char, node_color)

        packet_count = 2
        if self._mode == "thinking":
            packet_count = 6
        elif self._mode == "tool_execution":
            packet_count = 5
        elif self._mode == "memory_access":
            packet_count = 4

        for p in range(packet_count):
            edge_idx = (self._tick // 2 + p) % len(self.EDGE_INDEXES)
            a_idx, b_idx = self.EDGE_INDEXES[edge_idx]
            x0, y0 = node_positions[a_idx]
            x1, y1 = node_positions[b_idx]
            t = ((self._tick * (0.08 + (p * 0.01))) + p * 0.19) % 1.0
            px = int(round(x0 + (x1 - x0) * t))
            py = int(round(y0 + (y1 - y0) * t))
            put(px, py, "●", "#ffffff")

        # Subtle scanline/flicker texture.
        if self._tick % 2 == 0:
            for y in range(0, height, 2):
                for x in range(0, width, 3):
                    if grid[y][x] == " ":
                        put(x, y, "·", "#0d3540")

        lines: list[str] = []
        for y in range(height):
            out: list[str] = []
            active: str | None = None
            for x in range(width):
                c = color[y][x]
                if c != active:
                    if active is not None:
                        out.append("[/]")
                    if c is not None:
                        out.append(f"[{c}]")
                    active = c
                out.append(grid[y][x])
            if active is not None:
                out.append("[/]")
            lines.append("".join(out).rstrip())

        mode_label = self._mode.replace("_", " ").upper()
        status = (
            f"[#2a8f9e]MODE[/] [#5ce1e6]{mode_label}[/]  "
            f"[#2a8f9e]CORE[/] [#00ffff]ONLINE[/]"
        )
        legend = "[#00ffff]⬢[/] Core [#5ce1e6]●[/] Nodes [#ffffff]●[/] Packets [#2a8f9e]┄[/] Links"

        return (
            f"{section_title('PANTHEON CORE')}\n"
            f"{status}\n"
            f"{legend}\n\n"
            + "\n".join(lines)
            + "\n\n"
            f"{stat_row('Nodes', str(len(self.NODE_LABELS)))}  {stat_row('Edges', str(len(self.EDGE_INDEXES)))}\n"
            f"{stat_row('Profile', 'TRON C2')}  {stat_row('Scanline', 'active')}"
        )

    def _fallback_static_reactor(self) -> str:
        return (
            f"{section_title('PANTHEON CORE')}\n"
            "[#ffcc00]⚠ Fallback L1: static wireframe reactor[/]\n\n"
            "[#00aaff]            ◌◌◌[/]\n"
            "[#00aaff]         ◌◉     ◉◌[/]\n"
            "[#00ffff]            ⬢●⬢[/]\n"
            "[#00aaff]         ◌◉     ◉◌[/]\n"
            "[#00aaff]            ◌◌◌[/]\n\n"
            f"{stat_row('Mode', 'fallback-1')}  {stat_row('Status', 'degraded')}"
        )

    def _fallback_neural_only(self) -> str:
        phase = self._tick % 8
        rows = []
        for i in range(8):
            dot = "●" if i == phase else "◦"
            rows.append(f"[#5ce1e6]{dot}[/] [#2a8f9e]node-{i:02d}[/] [#00aaff]┄┄┄[/]")
        return (
            f"{section_title('PANTHEON CORE')}\n"
            "[#ffcc00]⚠ Fallback L2: animated neural graph[/]\n\n"
            + "\n".join(rows)
            + "\n\n"
            f"{stat_row('Mode', 'fallback-2')}  {stat_row('Status', 'degraded')}"
        )

    def _fallback_unicode_panel(self) -> str:
        return (
            f"{section_title('PANTHEON CORE')}\n"
            "[#ffcc00]⚠ Fallback L3: unicode panel[/]\n\n"
            "[#00ffff]┌────────────────────┐[/]\n"
            "[#00aaff]│  ◉  ⬢  ◉  ⬢  ◉   │[/]\n"
            "[#00aaff]│  ▣  ●  ◈  ●  ▣   │[/]\n"
            "[#00aaff]│  ◉  ⬢  ◉  ⬢  ◉   │[/]\n"
            "[#00ffff]└────────────────────┘[/]\n\n"
            f"{stat_row('Mode', 'fallback-3')}  {stat_row('Status', 'degraded')}"
        )

    def _fallback_disabled(self) -> str:
        return (
            f"{section_title('PANTHEON CORE')}\n"
            "[#ff4477]✖ Fallback L4: visualization disabled[/]\n"
            "[#2a8f9e]Terminal preserved. No functionality impacted.[/]\n\n"
            f"{stat_row('Mode', 'fallback-4')}  {stat_row('Status', 'disabled')}"
        )
