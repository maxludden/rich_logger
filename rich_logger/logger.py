"""Drop-in Rich-backed wrapper around :mod:`loguru`."""

from __future__ import annotations

from io import StringIO
from typing import Any, Callable

import loguru
from loguru import logger as loguru_logger
from rich.console import Console, RenderableType

from .config import RichLoggerConfig
from .sink import RICH_RENDERABLE_EXTRA, RichSink

_console: Console = Console()
_shared_logger: "RichLogger | None" = None


def get_console(console: Console | None = None) -> Console:
    """Return the shared Rich console.

    Args:
        console: Optional replacement console for future default sink setup.

    Returns:
        The active Rich console.
    """
    global _console
    if console is not None:
        _console = console
    return _console


def is_rich_renderable(value: Any) -> bool:
    """Return whether a value should be treated as a Rich renderable.

    Args:
        value: Message value passed to a logging method.

    Returns:
        ``True`` when the value exposes a Rich render protocol.
    """
    if isinstance(value, str | bytes):
        return False
    return hasattr(value, "__rich_console__") or hasattr(value, "__rich__")


def render_plain(renderable: RenderableType, width: int = 100) -> str:
    """Render a Rich object to plain terminal text.

    Args:
        renderable: Rich renderable to convert.
        width: Console width used for deterministic rendering.

    Returns:
        Plain text output with trailing newlines removed.
    """
    buffer = StringIO()
    console = Console(
        file=buffer,
        force_terminal=False,
        color_system=None,
        width=width,
        legacy_windows=False,
    )
    console.print(renderable)
    return buffer.getvalue().rstrip("\n")


class RichLogger:
    """Loguru-compatible logger that understands Rich renderables.

    Args:
        wrapped: Concrete Loguru logger instance to proxy.
        render_width: Width used when converting Rich renderables to plain text.
    """

    def __init__(
        self,
        wrapped: loguru.Logger | None = None,
        *,
        render_width: int = 100,
        opt_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a wrapped logger.

        Args:
            wrapped: Concrete Loguru logger. The module-level Loguru logger is
                used when omitted.
            render_width: Width used for plain text rendering.
            opt_kwargs: Loguru ``opt()`` keyword arguments to apply when logging.
        """
        self._logger = wrapped or loguru_logger
        self._render_width = render_width
        self._opt_kwargs = dict(opt_kwargs or {})

    @property
    def wrapped(self) -> loguru.Logger:
        """Return the underlying Loguru logger."""
        return self._logger

    def __getattr__(self, name: str) -> Any:
        """Forward unknown attributes to the wrapped Loguru logger.

        Args:
            name: Attribute name requested by the caller.

        Returns:
            Attribute from the underlying Loguru logger.
        """
        return getattr(self._logger, name)

    def _wrap(
        self,
        wrapped: loguru.Logger,
        *,
        opt_kwargs: dict[str, Any] | None = None,
    ) -> "RichLogger":
        """Wrap a derived Loguru logger.

        Args:
            wrapped: Derived Loguru logger returned by a chainable method.
            opt_kwargs: Optional replacement Loguru ``opt()`` keyword arguments.

        Returns:
            A new RichLogger preserving renderable support.
        """
        return type(self)(
            wrapped,
            render_width=self._render_width,
            opt_kwargs=self._opt_kwargs if opt_kwargs is None else opt_kwargs,
        )

    def _coerce_message(self, message: Any) -> tuple[Any, dict[str, Any]]:
        """Prepare a message and extra data for Loguru.

        Args:
            message: Value passed to a logging method.

        Returns:
            A pair of ``(message, extra)`` for Loguru.
        """
        if not is_rich_renderable(message):
            return message, {}
        plain = render_plain(message, width=self._render_width)
        return plain, {RICH_RENDERABLE_EXTRA: message}

    def _loguru_opt_kwargs(self, **overrides: Any) -> dict[str, Any]:
        """Return Loguru options with wrapper stack depth included.

        Args:
            **overrides: Option values replacing stored ``opt()`` options.

        Returns:
            Keyword arguments suitable for ``loguru.Logger.opt``.
        """
        options = {**self._opt_kwargs, **overrides}
        depth = options.get("depth", 0)
        if not isinstance(depth, int):
            depth = 0
        options["depth"] = depth + 2
        return options

    def _log_level(self, level: str | int, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a message at a concrete Loguru level.

        Args:
            level: Loguru level name or number.
            message: Message or Rich renderable to log.
            *args: Positional formatting arguments forwarded to Loguru.
            **kwargs: Keyword formatting arguments forwarded to Loguru.
        """
        plain_message, extra = self._coerce_message(message)
        target = self._logger.bind(**extra) if extra else self._logger
        target.opt(**self._loguru_opt_kwargs()).log(
            level,
            plain_message,
            *args,
            **kwargs,
        )

    def trace(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log ``message`` with the ``TRACE`` level."""
        self._log_level("TRACE", message, *args, **kwargs)

    def debug(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log ``message`` with the ``DEBUG`` level."""
        self._log_level("DEBUG", message, *args, **kwargs)

    def info(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log ``message`` with the ``INFO`` level."""
        self._log_level("INFO", message, *args, **kwargs)

    def success(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log ``message`` with the ``SUCCESS`` level."""
        self._log_level("SUCCESS", message, *args, **kwargs)

    def warning(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log ``message`` with the ``WARNING`` level."""
        self._log_level("WARNING", message, *args, **kwargs)

    def error(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log ``message`` with the ``ERROR`` level."""
        self._log_level("ERROR", message, *args, **kwargs)

    def critical(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log ``message`` with the ``CRITICAL`` level."""
        self._log_level("CRITICAL", message, *args, **kwargs)

    def exception(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log ``message`` with the ``ERROR`` level and current exception."""
        plain_message, extra = self._coerce_message(message)
        target = self._logger.bind(**extra) if extra else self._logger
        target.opt(**self._loguru_opt_kwargs(exception=True)).error(
            plain_message,
            *args,
            **kwargs,
        )

    def log(self, level: str | int, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log ``message`` with an arbitrary Loguru level.

        Args:
            level: Loguru level name or number.
            message: Message or Rich renderable to log.
            *args: Positional formatting arguments forwarded to Loguru.
            **kwargs: Keyword formatting arguments forwarded to Loguru.
        """
        self._log_level(level, message, *args, **kwargs)

    def add(self, *args: Any, **kwargs: Any) -> int:
        """Add a Loguru sink and return its handler id."""
        if args and callable(args[0]) and "format" not in kwargs:
            kwargs["format"] = "{message}"
        return self._logger.add(*args, **kwargs)

    def remove(self, *args: Any, **kwargs: Any) -> None:
        """Remove one or all Loguru handlers."""
        self._logger.remove(*args, **kwargs)

    def complete(self) -> Any:
        """Wait for queued or asynchronous Loguru sinks to finish."""
        return self._logger.complete()

    def catch(self, *args: Any, **kwargs: Any) -> Any:
        """Return Loguru's exception-catching decorator/context manager."""
        return self._logger.catch(*args, **kwargs)

    def configure(self, *args: Any, **kwargs: Any) -> list[int] | None:
        """Configure the underlying Loguru logger."""
        return self._logger.configure(*args, **kwargs)

    def disable(self, name: str) -> None:
        """Disable logging for a module name."""
        self._logger.disable(name)

    def enable(self, name: str) -> None:
        """Enable logging for a module name."""
        self._logger.enable(name)

    def level(self, *args: Any, **kwargs: Any) -> Any:
        """Create, update, or retrieve a Loguru level."""
        return self._logger.level(*args, **kwargs)

    def bind(self, **kwargs: Any) -> "RichLogger":
        """Bind contextual data and return a wrapped logger."""
        return self._wrap(self._logger.bind(**kwargs))

    def opt(self, *args: Any, **kwargs: Any) -> "RichLogger":
        """Apply Loguru options and return a wrapped logger."""
        if args:
            return self._wrap(self._logger.opt(*args, **kwargs))
        return self._wrap(self._logger, opt_kwargs={**self._opt_kwargs, **kwargs})

    def patch(
        self,
        patcher: Callable[[dict[str, Any]], None],
    ) -> "RichLogger":
        """Apply a Loguru record patcher and return a wrapped logger.

        Args:
            patcher: Callable mutating a Loguru record in place.

        Returns:
            Wrapped patched logger.
        """
        return self._wrap(self._logger.patch(patcher))


def _build_config(
    config: RichLoggerConfig | None = None,
    **overrides: Any,
) -> RichLoggerConfig:
    """Merge an optional config object with keyword overrides.

    Args:
        config: Base configuration, if any.
        **overrides: Field values that override the base configuration.

    Returns:
        Concrete Rich logger configuration.
    """
    data: dict[str, Any] = {}
    if config is not None:
        data.update(
            console=config.console,
            level=config.level,
            configure_default_sink=config.configure_default_sink,
            panel_padding=config.panel_padding,
            panel_expand=config.panel_expand,
            render_width=config.render_width,
        )
    data.update(overrides)
    return RichLoggerConfig(**data)


def get_logger(
    config: RichLoggerConfig | None = None,
    **overrides: Any,
) -> RichLogger:
    """Create a RichLogger, optionally configuring the default sink.

    Args:
        config: Optional base configuration object.
        **overrides: Configuration values accepted by
            :class:`RichLoggerConfig`.

    Returns:
        A configured RichLogger wrapper.
    """
    resolved = _build_config(config, **overrides)
    console = get_console(resolved.console)
    wrapped = RichLogger(loguru_logger, render_width=resolved.render_width)
    if resolved.configure_default_sink:
        wrapped.remove()
        wrapped.add(
            RichSink(
                console=console,
                padding=resolved.panel_padding,
                expand=resolved.panel_expand,
            ),
            level=resolved.level,
            format="{message}",
            colorize=False,
            backtrace=True,
            diagnose=True,
        )
    return wrapped


def setup_logger(
    config: RichLoggerConfig | None = None,
    **overrides: Any,
) -> RichLogger:
    """Configure and return the shared RichLogger.

    Args:
        config: Optional base configuration object.
        **overrides: Configuration values accepted by
            :class:`RichLoggerConfig`.

    Returns:
        The shared RichLogger instance.
    """
    global _shared_logger
    _shared_logger = get_logger(config, **overrides)
    return _shared_logger


logger: RichLogger = setup_logger()
log: RichLogger = logger

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
