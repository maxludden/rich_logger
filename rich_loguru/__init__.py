"""Rich-enhanced drop-in replacement for loguru.logger."""

from importlib import import_module
from typing import Any

from .config import LoggerConfig
from .logger import get_console, get_logger, get_progress

_core_logger: Any = None


def setup_logger(*args, **kwargs):
    """Set up the core logger."""
    global _core_logger  # pylint: disable=global-statement
    if _core_logger is None:
        _core_logger = import_module(".logger", __name__)
    return _core_logger.setup_logger(*args, **kwargs)


log = setup_logger()

__all__ = [
    "log",
    "setup_logger",
    "LoggerConfig",
    "get_console",
    "get_logger",
    "get_progress",
]
