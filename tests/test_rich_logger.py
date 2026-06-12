"""Tests for the Rich-backed Loguru drop-in API."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from rich_logger import RichLogger, get_logger, logger, log, setup_logger


@pytest.fixture()
def text_console() -> Console:
    """Return a deterministic recording console for Rich sink assertions."""
    buffer = StringIO()
    return Console(
        file=buffer,
        force_terminal=False,
        color_system=None,
        width=100,
        record=True,
    )


def test_package_exports_logger_and_log_alias() -> None:
    """Expose ``logger`` as canonical API and ``log`` as compatibility alias."""
    assert isinstance(logger, RichLogger)
    assert logger is log


def test_logging_methods_delegate_to_loguru_sinks() -> None:
    """Send every standard Loguru level method through a callable sink."""
    seen: list[str] = []
    test_logger = get_logger(configure_default_sink=False)
    test_logger.remove()
    handler_id = test_logger.add(
        lambda message: seen.append(message.record["level"].name),
        format="{message}",
        level="TRACE",
    )

    try:
        test_logger.trace("trace")
        test_logger.debug("debug")
        test_logger.info("info")
        test_logger.success("success")
        test_logger.warning("warning")
        test_logger.error("error")
        test_logger.critical("critical")
        test_logger.log("INFO", "log")
    finally:
        test_logger.remove(handler_id)

    assert seen == [
        "TRACE",
        "DEBUG",
        "INFO",
        "SUCCESS",
        "WARNING",
        "ERROR",
        "CRITICAL",
        "INFO",
    ]


def test_bind_opt_and_patch_keep_rich_logger_wrapper() -> None:
    """Return wrapped loggers from chainable Loguru APIs."""
    base = get_logger(configure_default_sink=False)
    bound = base.bind(request_id="abc")
    opted = bound.opt(depth=0)
    patched = opted.patch(lambda record: record["extra"].update(patched=True))

    assert isinstance(bound, RichLogger)
    assert isinstance(opted, RichLogger)
    assert isinstance(patched, RichLogger)


def test_opt_options_are_preserved_when_logging() -> None:
    """Preserve Loguru options after ``opt()`` returns a RichLogger."""
    seen: list[str] = []
    test_logger = get_logger(configure_default_sink=False)
    test_logger.remove()
    handler_id = test_logger.add(lambda message: seen.append(str(message)))

    try:
        test_logger.opt(lazy=True).info("value {}", lambda: "computed")
    finally:
        test_logger.remove(handler_id)

    assert seen == ["value computed\n"]


def test_rich_sink_renders_panel_with_record_metadata(text_console: Console) -> None:
    """Render default console output as a Rich panel with Loguru metadata."""
    configured = setup_logger(console=text_console, level="INFO")
    configured.info("plain message")

    output = text_console.export_text(clear=False)

    assert "INFO" in output
    assert "test_rich_logger" in output
    assert "test_rich_sink_renders_panel_with_record_metadata" in output
    assert "plain message" in output


def test_rich_renderable_uses_panel_in_console_sink(text_console: Console) -> None:
    """Render the original Rich object in the console sink."""
    configured = setup_logger(console=text_console, level="INFO")
    configured.info(Panel("inside renderable", title="Renderable"))

    output = text_console.export_text(clear=False)

    assert "Renderable" in output
    assert "inside renderable" in output
    assert "INFO" in output


def test_rich_renderable_becomes_plain_text_for_regular_sinks(tmp_path: Path) -> None:
    """Render Rich objects to plain text for non-console Loguru sinks."""
    table = Table("Name")
    table.add_row("Ada")

    test_logger = get_logger(configure_default_sink=False)
    test_logger.remove()
    log_file = tmp_path / "plain.log"
    handler_id = test_logger.add(log_file, format="{message}", level="INFO")

    try:
        test_logger.info(table)
    finally:
        test_logger.remove(handler_id)

    contents = log_file.read_text(encoding="utf-8")
    assert "Name" in contents
    assert "Ada" in contents
    assert "Table(" not in contents


def test_add_remove_configure_complete_passthrough() -> None:
    """Forward core Loguru configuration methods to the wrapped logger."""
    seen: list[str] = []
    test_logger = get_logger(configure_default_sink=False)
    test_logger.remove()
    handler_id = test_logger.add(lambda message: seen.append(str(message)), level="INFO")

    test_logger.info("before remove")
    test_logger.remove(handler_id)
    test_logger.info("after remove")
    completion: Any = test_logger.complete()

    assert len(seen) == 1
    assert "before remove" in seen[0]
    assert completion is None or hasattr(completion, "__await__")
