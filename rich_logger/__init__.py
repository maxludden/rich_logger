"""Rich-backed drop-in replacement for :data:`loguru.logger`."""

from __future__ import annotations

from .config import RichLoggerConfig
from .logger import (
    RichLogger,
    get_console,
    get_logger,
    is_rich_renderable,
    log,
    logger,
    render_plain,
    setup_logger,
)
from .sink import RICH_RENDERABLE_EXTRA, RichSink

__all__ = [
    "RICH_RENDERABLE_EXTRA",
    "RichLogger",
    "RichLoggerConfig",
    "RichSink",
    "get_console",
    "get_logger",
    "is_rich_renderable",
    "log",
    "logger",
    "render_plain",
    "setup_logger",
]
