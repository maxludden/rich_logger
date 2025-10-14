"""Example of dynamic logger configuration updates."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import loguru

import rich_loguru.logger as logger_module
from rich_loguru import log, setup_logger
from rich_loguru.config import LoggerConfig
from rich_loguru.logger import get_console


def update_logger_config(**kwargs: Any) -> loguru.Logger:
    """
    Dynamically update logger configuration.

    Args:
        **kwargs: Configuration parameters to update

    Returns:
        loguru.Logger: The reconfigured logger instance
    """
    # Get current config or create default
    current_config: LoggerConfig | None = getattr(logger_module, "_logger_config", None)
    if current_config is None:
        current_config = LoggerConfig()

    # Create new config with updates
    new_config: LoggerConfig = replace(current_config, **kwargs)

    # Reconfigure logger
    return setup_logger(new_config)


def main() -> None:
    """Demonstrate dynamic configuration updates."""

    # Initial logging
    log.info("Initial configuration")

    # Update to enable recording and verbose mode
    updated_log: loguru.Logger = update_logger_config(
        record=True, verbose=True, level="DEBUG"
    )

    updated_log.debug("Debug message with new config")
    updated_log.info("Info message with recording enabled")

    # Update console settings directly
    get_console(show_locals=True)
    updated_log.info("Console now shows locals in tracebacks")

    # Monkey patch specific settings
    logger_module.VERBOSE = False
    updated_log.info("Verbose mode disabled via monkey patch")


if __name__ == "__main__":
    main()
