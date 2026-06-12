"""Example showing Rich Logger reconfiguration."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rich.console import Console
from rich.panel import Panel

from rich_logger import RichLogger, RichLoggerConfig, setup_logger


def build_recording_logger() -> tuple[RichLogger, Console]:
    """Create a logger that writes Rich output to an in-memory console.

    Returns:
        A configured logger and the recording console it uses.
    """
    buffer = StringIO()
    console = Console(file=buffer, record=True, width=100)
    config = RichLoggerConfig(console=console, level="DEBUG", panel_padding=(1, 2))
    return setup_logger(config), console


def main() -> None:
    """Demonstrate runtime configuration and Rich renderable logging."""
    logger, console = build_recording_logger()

    logger.debug("Debug output is visible after reconfiguration")
    logger.info(Panel("Rich renderables are preserved in the console sink"))
    handler_id = logger.add(
        "logs/dynamic-config.log",
        format="{level} | {message}",
        level="INFO",
    )
    try:
        logger.info(Panel("This message is plain text in the file sink"))
    finally:
        logger.remove(handler_id)

    console.export_text(clear=False)


if __name__ == "__main__":
    main()
