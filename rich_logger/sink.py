"""Rich panel sink for Loguru messages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Final

from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

RICH_RENDERABLE_EXTRA: Final[str] = "rich_logger_renderable"


@dataclass(slots=True)
class RichSink:
    """Callable Loguru sink that renders records as Rich panels.

    Args:
        console: Rich console used for output.
        padding: Padding applied to each panel as ``(vertical, horizontal)``.
        expand: Whether panels should expand to the console width.
    """

    console: Console
    padding: tuple[int, int] = (0, 1)
    expand: bool = True

    LEVEL_STYLES: ClassVar[Final[dict[str, str]]] = {
        "TRACE": "dim white",
        "DEBUG": "cyan",
        "INFO": "blue",
        "SUCCESS": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold white on red",
    }

    def __call__(self, message: Any) -> None:
        """Render one Loguru message.

        Args:
            message: Loguru message object received by custom sinks.
        """
        self.console.print(self.build_panel(message.record))

    def build_panel(self, record: dict[str, Any]) -> Panel:
        """Build a Rich panel from a Loguru record.

        Args:
            record: Loguru record dictionary from ``message.record``.

        Returns:
            A Rich panel containing the log message or original renderable.
        """
        level = record["level"].name
        style = self.LEVEL_STYLES.get(level, "white")
        module = str(record.get("module") or record.get("name") or "<module>")
        function = str(record.get("function") or "<function>")
        timestamp = record["time"].strftime("%H:%M:%S.%f")[:-3]
        title = Text.assemble(
            (" ", style),
            (level, f"bold {style}"),
            (" | ", "dim"),
            (f"{module}.{function}", "bold"),
            (" ", style),
        )
        subtitle = Text(timestamp, style="dim")
        body = self._record_renderable(record)

        return Panel(
            body,
            title=title,
            title_align="left",
            subtitle=subtitle,
            subtitle_align="right",
            border_style=Style.parse(style),
            padding=self.padding,
            expand=self.expand,
        )

    def _record_renderable(self, record: dict[str, Any]) -> RenderableType:
        """Return the Rich object that should appear inside a panel.

        Args:
            record: Loguru record dictionary.

        Returns:
            The original Rich renderable when available, otherwise styled text.
        """
        extra = record.get("extra", {})
        renderable = extra.get(RICH_RENDERABLE_EXTRA)
        if renderable is not None:
            return renderable

        level = record["level"].name
        style = self.LEVEL_STYLES.get(level, "white")
        message = str(record.get("message", ""))
        exception = record.get("exception")
        if exception is None:
            return Text(message, style=style)
        return Group(Text(message, style=style), Text(str(exception), style="red"))
