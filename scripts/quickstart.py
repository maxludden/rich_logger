"""Quickstart example for Rich Logger."""

from __future__ import annotations

from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rich.panel import Panel

from rich_logger import logger


def main() -> None:
    """Log plain text, a Rich renderable, a file sink, and a chained message."""
    logger.info("Hello, colourful world!")
    logger.info(Panel("This renderable is shown inside the log panel", title="Rich"))

    log_file = Path("logs/quickstart.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler_id = logger.add(log_file, format="{level} | {message}", level="INFO")
    try:
        logger.info(Panel("Plain text is written to the file sink", title="File"))
    finally:
        logger.remove(handler_id)

    logger.bind(example="quickstart").opt(depth=0).success("All systems go")


if __name__ == "__main__":
    main()
