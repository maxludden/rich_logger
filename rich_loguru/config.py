"""Configuration helpers for the rich logger."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

__all__ = ["LoggerConfig", "load_config_from_env"]

_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
_FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}


def _coerce_bool(value: str, default: bool) -> bool:
    candidate = value.strip().lower()
    if candidate in _TRUE_VALUES:
        return True
    if candidate in _FALSE_VALUES:
        return False
    return default


def _coerce_padding(value: str, default: Tuple[int, int]) -> Tuple[int, int]:
    fields = [item for item in value.replace(",", " ").split() if item]
    if len(fields) != 2:
        return default
    try:
        first, second = (int(part) for part in fields)
    except ValueError:
        return default
    return first, second


def _coerce_json(value: str) -> List[Dict[str, Any]]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        return [parsed]
    return []


def _coerce_path(value: Optional[str]) -> Optional[Path]:
    if value is None or not value.strip():
        return None
    return Path(value).expanduser()


@dataclass
class LoggerConfig:
    """Runtime configuration for :mod:`core.logger`."""

    level: str | int = "INFO"
    verbose: bool = False
    track_run: bool = True
    record: bool = False
    show_locals: bool = False
    padding: Tuple[int, int] = (1, 2)
    expand: bool = True
    additional_sinks: List[Dict[str, Any]] = field(default_factory=list)
    logs_dir: Optional[Path] = None
    run_file: Optional[Path] = None
    env_prefix: str = "RICH_LOGGER_"

    def logger_kwargs(self) -> Dict[str, Any]:
        """
        Return keyword arguments suitable for :func:`core.logger.get_logger`.
        """
        return {
            "level": self.level,
            "verbose": self.verbose,
            "track_run": self.track_run,
            "additional_sinks": self.additional_sinks or None,
            "padding": self.padding,
            "expand": self.expand,
        }


def load_config_from_env(prefix: str = "RICH_LOGGER_") -> LoggerConfig:
    """
    Build a :class:`LoggerConfig` instance using environment variables.

    Supported variables (case insensitive):
        {prefix}LEVEL -> str
        {prefix}VERBOSE -> bool
        {prefix}TRACK_RUN -> bool
        {prefix}RECORD -> bool
        {prefix}SHOW_LOCALS -> bool
        {prefix}PADDING -> "int int" or "int,int"
        {prefix}EXPAND -> bool
        {prefix}LOGS_DIR -> path
        {prefix}RUN_FILE -> path
        {prefix}ADDITIONAL_SINKS -> JSON list/dict
    """

    data: Dict[str, Any] = {"env_prefix": prefix}

    if (value := os.getenv(f"{prefix}LEVEL")) is not None:
        data["level"] = value

    if (value := os.getenv(f"{prefix}VERBOSE")) is not None:
        data["verbose"] = _coerce_bool(value, False)

    if (value := os.getenv(f"{prefix}TRACK_RUN")) is not None:
        data["track_run"] = _coerce_bool(value, True)

    if (value := os.getenv(f"{prefix}RECORD")) is not None:
        data["record"] = _coerce_bool(value, False)

    if (value := os.getenv(f"{prefix}SHOW_LOCALS")) is not None:
        data["show_locals"] = _coerce_bool(value, False)

    if (value := os.getenv(f"{prefix}PADDING")) is not None:
        data["padding"] = _coerce_padding(value, (1, 2))

    if (value := os.getenv(f"{prefix}EXPAND")) is not None:
        data["expand"] = _coerce_bool(value, True)

    logs_dir = _coerce_path(os.getenv(f"{prefix}LOGS_DIR"))
    if logs_dir is not None:
        data["logs_dir"] = logs_dir

    run_file = _coerce_path(os.getenv(f"{prefix}RUN_FILE"))
    if run_file is not None:
        data["run_file"] = run_file

    if (value := os.getenv(f"{prefix}ADDITIONAL_SINKS")) is not None:
        data["additional_sinks"] = _coerce_json(value)

    return LoggerConfig(**data)
