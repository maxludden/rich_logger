"""Configuration models for Rich Logger."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rich.console import Console


@dataclass(frozen=True, slots=True)
class RichLoggerConfig:
    """Runtime configuration for the shared Rich-backed logger.

    Args:
        console: Optional Rich console used by the default panel sink.
        level: Minimum Loguru level for the default Rich console sink.
        configure_default_sink: Whether to replace existing handlers with the
            default Rich panel sink.
        panel_padding: Padding applied to Rich panels as ``(vertical,
            horizontal)``.
        panel_expand: Whether Rich panels should expand to the console width.
        render_width: Width used when rendering Rich objects to plain text for
            non-console sinks.
    """

    console: Console | None = None
    level: str | int = "INFO"
    configure_default_sink: bool = True
    panel_padding: tuple[int, int] = (0, 1)
    panel_expand: bool = True
    render_width: int = 100

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> RichLoggerConfig:
        """Build a config object from keyword arguments.

        Args:
            **kwargs: Field values accepted by :class:`RichLoggerConfig`.

        Returns:
            A concrete configuration object.
        """
        return cls(**kwargs)
