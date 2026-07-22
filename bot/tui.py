# tui.py
#
# formatting system for bunkerOS
# handles CLI outputs to follow inner logic.

class BunkerTUI:
    @classmethod
    def wrap(cls, text: str) -> str:
        return f"<pre>{text}</pre>"

    @classmethod
    def clean_screen(cls) -> str:
        empty_lines = "\n" * 45
        stretcher = "\xa0" * 60
        return cls.wrap(f"{stretcher}{empty_lines}\n~_>|")

    @classmethod
    def action(cls, text: str) -> str:
        return cls.wrap(f"^_> {text.lower()}")

    @classmethod
    def success(cls, text: str, latency: int | None = None) -> str:
        lines = [f"~~ {text.lower()}"]
        if latency is not None:
            lines.append(f"~~ {latency} ms")

        return cls.wrap("\n".join(lines))

    @classmethod
    def error(cls, reason: str, nodes: dict[str, bool],  latency: int | None = None) -> str:
        lines = [f"!_> {reason.lower()}"]
        if latency is not None:
            lines.append(f"~~ {latency} ms")

        if nodes is not None:
            lines.append("")
            lines.append("ran diagnostics:")
            lines.extend(cls._format_nodes(nodes))

        return cls.wrap("\n".join(lines))

    @classmethod
    def fatal(cls, reason: str, latency: int | None = None) -> str:
        lines = [f"bunkerOS :: err"]

        lines.append("")
        lines.append(f"### {reason.lower()}")

        return cls.wrap("\n".join(lines))

    @classmethod
    def box(cls, title: str, lines: list[str], footer: str = "ready.") -> str:
        """automatically builds ascii styled boxes"""
        content = [
            f"+-- [ bunkerOS :: {title.lower()} ] --+",
            "|"
        ]

        for line in lines:
            if line.startswith(" "):
                content.append(f"|{line.lower()}")
            else:
                content.append(f"|-- {line.lower()}")

        content.append("|")
        content.append(f"+-- {footer.lower()}")

        return cls.wrap("\n".join(content))

    @classmethod
    def _format_nodes(cls, nodes: dict[str, bool]) -> list[str]:
        lines = []
        max_len = max(len(key) for key in nodes.keys()) if nodes else 0


        for key, is_up in nodes.items():
            icon = "[x]" if is_up else "[#]"
            status = "intact" if is_up else "connection failed"

            lines.append(f"- {icon} {key.lower():<{max_len}} :: {status}")

        return lines

    @classmethod
    def status_grid(cls, nodes: dict[str, bool], latency: int | None = None) -> str:
        lines = []
        if latency is not None:
            lines.append("~~ routing...")
            lines.append(f"~~ {latency} ms.")
            lines.append("")

        lines.append("nodes:")
        lines.extend(cls._format_nodes(nodes))

        return cls.wrap("\n".join(lines))

    @classmethod
    def welcome(cls):
        lines = [
            "bunkerOS v0.1a :: (telegram-tty1)",
            "",
            "auth ok. still standing by.",
            "",
            "/help available."
        ]

        return cls.wrap("\n".join(lines))

    @classmethod
    def executing(cls):
        return cls.wrap("^_> executing...")
