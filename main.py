"""Small demonstration entrypoint for Rich Logger."""

from __future__ import annotations

from rich.panel import Panel

from rich_logger import logger


def main() -> None:
    """Log a few example messages."""
    logger.trace("Trace message")
    logger.info("Hello, colourful world!")
    logger.info(Panel("Panels can be logged directly", title="Renderable"))
    logger.success("All systems go")


if __name__ == "__main__":
    main()
