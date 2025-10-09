"""Compatibility shim that re-exports the logger implementation from rich_logger.logger."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Iterable, List, Optional


def _safe_import_core() -> Any:
    try:
        return import_module("rich_logger.logger")
    except ImportError as exc:  # pragma: no cover - defensive guard
        raise ImportError(
            "Unable to import 'rich_logger.logger'. Ensure the rich_logger package is installed "
            "and importable."
        ) from exc


def _safe_import_config() -> Optional[Any]:
    try:
        module = import_module("rich_logger.config")
    except ImportError:
        return None
    return getattr(module, "LoggerConfig", None)


_core_logger = _safe_import_core()
LoggerConfig = _safe_import_config()


def _collect_exports(names: Iterable[str]) -> List[str]:
    exports: List[str] = []
    for name in names:
        if hasattr(_core_logger, name):
            exports.append(name)
    return exports


__doc__ = getattr(_core_logger, "__doc__", __doc__)

core_all = getattr(_core_logger, "__all__", [])
_exports = _collect_exports(core_all)

if LoggerConfig is not None and "LoggerConfig" not in _exports:
    _exports.append("LoggerConfig")
if "log" not in _exports:
    _exports.append("log")
if "get_console" not in _exports:
    _exports.append("get_console")
if "get_logger" not in _exports:
    _exports.append("get_logger")
if "get_progress" not in _exports:
    _exports.append("get_progress")

# Preserve order and remove duplicates without using dict.fromkeys to avoid analyzer warnings.
_seen = set()
__all__ = []
for _e in _exports:
    if _e not in _seen:
        _seen.add(_e)
        __all__.append(_e) # type: ignore[PLW2901]
del _seen

# Expose selected dunder attributes that callers may rely on.
__version__ = getattr(_core_logger, "__version__", None)
__author__ = getattr(_core_logger, "__author__", None)

# Populate the module namespace with vetted attributes from core.logger.
for _name in __all__:
    if _name == "LoggerConfig":
        continue
    if _name == "log":
        continue
    globals()[_name] = getattr(_core_logger, _name)

if LoggerConfig is not None:
    globals()["LoggerConfig"] = LoggerConfig


_log_instance: Optional[Any] = getattr(_core_logger, "log", None)
_log_error: Optional[BaseException] = None


def _initialise_log() -> Any:
    global _log_instance, _log_error  # noqa: PLW0603

    if _log_instance is not None:
        return _log_instance
    if _log_error is not None:
        raise RuntimeError(
            "A previous attempt to initialise the log instance failed."
        ) from _log_error

    setup = getattr(_core_logger, "setup_logger", None)
    if not callable(setup):
        _log_error = AttributeError(
            "The core logger module does not expose a 'setup_logger' callable."
        )
        raise RuntimeError("Unable to construct a log instance.") from _log_error

    try:
        _log_instance = setup()
    except Exception as exc:  # pragma: no cover - passthrough to caller
        _log_error = exc
        raise RuntimeError("Failed to initialise the log instance via setup_logger().") from exc

    return _log_instance


class _LogProxy:
    """Lazily resolve the underlying loguru logger on first use."""

    def __getattr__(self, item: str) -> Any:
        logger = _initialise_log()
        return getattr(logger, item)


log = _log_instance if _log_instance is not None else _LogProxy()
