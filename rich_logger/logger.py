"""Create a rich.console.Console sink for a loguru.Logger.
This module provides a custom sink for the loguru logger that uses the rich
library to format and display log messages in a visually appealing way. It also
includes functions to set up logging, manage run counts, and handle log file
creation and cleanup.

It is designed to be used in Python projects that require structured and colorful
logging output, especially for long-running processes or applications where
tracking progress and errors is important.

The module includes:
- A custom RichSink class that formats log messages with colors and styles.
- Functions to create and configure a rich console and progress bar.
- Functions to find the current working directory and manage log files.
- A function to increment and write the run count to a file.
- A function to handle cleanup and log file management on exit.
"""

from __future__ import annotations

import atexit
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

import loguru
from loguru import logger
from rich.console import Console
from rich.errors import MarkupError
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.style import Style
from rich.text import Text as RichText
from rich.traceback import install as tr_install
from rich_gradient.rule import Rule
from rich_gradient.text import Text

__all__ = [
    "get_console",
    "get_logger",
    "get_progress",
    "find_cwd",
    "CWD",
    "LOGS_DIR",
    "RUN_FILE",
    "FORMAT",
    "trace_sink",
    "RichSink",
    "on_exit",
    "setup",
    "read_run_from_file",
    "write_run_to_file",
    "increment_run_and_write_to_file",
]

__version__ = "0.2.1"
__author__ = "Max Ludden"
FORMAT: str = (
    "{time:hh:mm:ss.SSS} | {file.name: ^12} | Line {line: ^9} | {level:^11} ➤ {message}"
)
PLAIN_FORMAT: str = FORMAT.replace("{message}", "{extra[plain_message]}")

VERBOSE: bool = False
TRACK_RUN: bool = True
HandlerConfig = Dict[str, Any]


def _strip_rich_markup(message: Any) -> str:
    """
    Convert a rich-markup string into plain text for log file output.
    Falls back to a simple string cast if markup parsing fails.
    """
    text = str(message)
    try:
        return RichText.from_markup(text).plain
    except MarkupError:
        return RichText(text).plain


def _plain_message_patcher(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure each log record carries a plain-text version of the message.
    """
    record.setdefault("extra", {})
    record["extra"]["plain_message"] = _strip_rich_markup(record.get("message", ""))
    return record


# Log level names for validation
_LEVEL_NAMES = [
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
]

logger.configure(patcher=_plain_message_patcher)  # type: ignore
_log = logger.bind(file="logger")
_log.remove()
_log.add(sink="logs/trace.log", level="TRACE", format=PLAIN_FORMAT)


def get_console(
    console: Optional[Console] = None,
    record: bool = False,
    show_locals: bool = False
) -> Console:
    """
    Initialize and return a Rich console.

    Args:
        record (bool): Whether to record console output.
        show_locals (bool): Whether to show local variables in tracebacks.
        console (Optional[Console]): An optional existing Rich console (unused).

    Returns:
        Console: A configured Rich console.
    """
    _log.trace(f"Entered get_console({console=})")
    if console is not None:
        _log.trace("\tUsing supplied console...")
        _console = console
    else:
        _log.trace("\tNo supplied console. Generating console...")
        _console = Console(record=record)
    tr_install(console=_console, show_locals=show_locals)
    _log.trace("Leaving [b #0f0]get_console[/][b #fff]()[/]...")
    return _console


_console = get_console()


def get_progress(console: Optional[Console] = None) -> Progress:
    """
    Initialize and return a Rich progress bar.

    Args:
        console (Optional[Console]): An optional existing Rich console.
    Returns:
        Progress: A configured Rich progress bar.
    """
    if console is None:
        console = _console
    progress = Progress(
        SpinnerColumn(spinner_name="point"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        MofNCompleteColumn(),
        console=console,
        expand=True,
        refresh_per_second=30,
        transient=True,
    )
    return progress


def find_cwd(
    start_dir: Path = Path(__file__).parent.parent, verbose: bool = False
) -> Path:
    """
    Find the current working directory by walking upward until a 'pyproject.toml' is found.

    Args:
        start_dir (Path): The starting directory.
        verbose (bool): If True, prints the found directory in a styled panel.

    Returns:
        Path: The current working directory.
    """
    cwd: Path = start_dir
    while not (cwd / "pyproject.toml").exists():
        cwd = cwd.parent
        if cwd == Path.home():
            break
    if verbose:
        console = _console
        console.line(2)
        panel_title = Text(
            "Current Working Directory",
            colors=[
                "#ff005f",
                "#ff00af",
                "#ff00ff",
            ],
            style="bold",
        )
        console.print(
            Panel(
                f"[i #5f00ff]{cwd.resolve()}",
                title=panel_title,
            )
        )
        console.line(2)
    return cwd


# Constants and paths
CWD: Path = find_cwd()
LOGS_DIR: Path = CWD / "logs"
RUN_FILE: Path = LOGS_DIR / "run.txt"


def trace_sink() -> Dict[str, Any]:
    """
    Return the configuration for the trace sink.
    Returns:
        Dict[str, Any]: The trace sink configuration.
    """
    return {
        "sink": str((LOGS_DIR / "trace.log").resolve()),
        "format": PLAIN_FORMAT,
        "level": "TRACE",
        "backtrace": True,
        "diagnose": True,
        "colorize": False,
        "mode": "w",
    }


def setup(console: Optional[Console] = None) -> Optional[int]:
    """
    Setup the logger by creating necessary directories and files.

    Returns:
        Optional[int]: The run count (read from the run file), or None if run tracking is disabled.
    """
    if console is None:
        console = _console
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True)
        console.print(f"Created Logs Directory: {LOGS_DIR}")
    if not TRACK_RUN:
        console.print("[i #af99ff]Setup logger. Disabling run tracking.[/]")
        return None
    if not RUN_FILE.exists():
        with open(RUN_FILE, "w", encoding="utf-8") as f:
            f.write("0")
            console.print("Created Run File, set to 0")
    with open(RUN_FILE, "r", encoding="utf-8") as f:
        run = int(f.read())
    return run


def read_run_from_file(console: Optional[Console] = None) -> Optional[int]:
    """
    Read the run count from the run file.

    Returns:
        Optional[int]: The run count, or None if tracking is disabled.
    """
    if console is None:
        console = _console
    if not TRACK_RUN:
        return None
    console = get_console()
    if not RUN_FILE.exists():
        console.print("[b #ff0000]Run File Not Found[/][i #ff9900] – Creating...[/]")
        setup()
    with open(RUN_FILE, "r", encoding="utf-8") as f:
        run = int(f.read())
    return run


def get_default_sinks(
    console: Optional[Console],
    run: Optional[int],
    level: int,
    padding: Tuple[int, int] = (0, 1),
    expand: bool = False,
) -> List[HandlerConfig]:
    """
    Return the default sinks for the logger.
    Args:
        console (Optional[Console]): The Rich console for the RichSink.
        run (Optional[int]): The run count.
        level (int): The log level as an integer.
    Returns:
        List[Dict[str, Any]]: A list of sink configuration dictionaries.
    """
    if console is None:
        console = _console
    return [
        {
            "sink": RichSink(
                console=console, run=run, record=False, padding=padding, expand=expand
            ),
            "format": "{message}",
            "level": max(level, _validate_level("INFO")),
            "backtrace": True,
            "diagnose": True,
            "colorize": False,
        },
        {
            "sink": str(LOGS_DIR / "trace.log"),
            "format": PLAIN_FORMAT,
            "level": "TRACE",
            "backtrace": True,
            "diagnose": True,
            "colorize": False,
            "mode": "a",  # Use append mode instead of write mode
            "retention": "30 minutes",
        },
    ]


def _validate_level(level: str | int) -> int:
    """
    Validate the log level and convert it to an integer.
    Args:
        level (str|int): The logging level. Can be a string
            (e.g., "DEBUG", "INFO", etc.) or an integer (0-50).
    Returns:
        Optional[int]: The validated log level as an integer,
            or None if invalid.
    Raises:
        TypeError: If the log level is not a string or an integer.
        ValueError: If the log level is not valid.
    """
    if isinstance(level, int) and (0 < level > 50):
        raise ValueError(f"Log level integer must be between 0 and 50, got {level}.")
    if isinstance(level, int) and (0 >= level >= 50):
        return level
    if not isinstance(level, str):
        raise TypeError(f"Log level must be a string or an integer, got {type(level)}.")
    _level = level.upper()
    if _level not in _LEVEL_NAMES:
        raise ValueError(
            f"Invalid log level: {level!r}. Must be one of: {', '.join(_LEVEL_NAMES)}."
        )
    match _level:
        case "TRACE":
            return 5
        case "DEBUG":
            return 10
        case "INFO":
            return 20
        case "SUCCESS":
            return 25
        case "WARNING":
            return 30
        case "ERROR":
            return 40
        case "CRITICAL":
            return 50
        case _:
            raise ValueError(
                f"Unable to parse log level: {level!r}. Must be one of: {', '.join(_LEVEL_NAMES)}."
            )


def get_logger(
    console: Optional[Console] = None,
    level: str | int = "INFO",
    verbose: bool = False,
    track_run: bool = True,
    additional_sinks: Optional[List[Dict[str, Any]]] = None,
    padding: Tuple[int, int] = (1, 2),
    expand: bool = True,
) -> loguru.Logger:
    """
    Initialize and return a Loguru logger.

    Args:
        console (Optional[Console]): An optional existing Rich console.
            If None, a new one is created.
        level (str|int): The logging level (e.g., "DEBUG", "INFO", etc.) or an integer (0-50).
        verbose (bool): If True, enables verbose logging.
        track_run (bool): If True, enables run tracking.
        additional_sinks (Optional[List[Dict[str, Any]]]): Extra sinks to add to the logger.

    Returns:
        Logger: A configured Loguru logger.
    """
    if console is None:
        console = _console
    run = read_run_from_file() if track_run else None

    # Validate the log level
    _level = _validate_level(level)
    sinks = get_default_sinks(
        console=console, run=run, level=_level, padding=padding, expand=expand
    )
    if additional_sinks:
        sinks.extend(additional_sinks)

    log = loguru.logger.bind(sink="rich")
    log.remove()
    log.configure(
        handlers=cast(Any, sinks),
        extra={"run": run, "rich": "", "verbose": verbose, "padding": ()},
        patcher=_plain_message_patcher,  # type: ignore
    )
    return log


def write_run_to_file(run: int, verbose: bool = False) -> None:
    """
    Write the run count to the run file.

    Args:
        run (int): The run count to write.
        verbose (bool): If True, logs a trace message.
    """
    if verbose:
        log = get_logger()
        log.trace("Writing run count...")
    with open(RUN_FILE, "w", encoding="utf-8") as f:
        f.write(str(run))


def increment_run_and_write_to_file() -> Optional[int]:
    """
    Increment the run count, write it to the file, and return the new count.

    Returns:
        Optional[int]: The incremented run count, or None if tracking is disabled.
    """
    if not TRACK_RUN:
        return None
    log = get_logger()
    log.trace("Incrementing run count...")
    run = read_run_from_file()
    assert run is not None, "Run count not found in file."
    run += 1
    write_run_to_file(run)
    return run


class RichSink:
    """
    A custom Loguru sink that uses Rich to print styled log messages.

    Attributes:
        LEVEL_STYLES (Dict[str, Style]): Styles for each log level.
        GRADIENTS (Dict[str, List[Color]]): Gradients for log level titles.
        MSG_COLORS (Dict[str, List[Color]]): Gradients for log message text.
        run (Optional[int]): The current run number.
        console (Console): The Rich console used for output.
    """

    LEVEL_STYLES: Dict[str, Style] = {
        "TRACE": Style(bold=True),
        "DEBUG": Style(color="#aaaaaa"),
        "INFO": Style(color="#00afff"),
        "SUCCESS": Style(bold=True, color="#00ff00"),
        "WARNING": Style(bold=True, color="#ffaf00"),
        "ERROR": Style(bold=True, color="#ff5000"),
        "CRITICAL": Style(bold=True, color="#ff0000"),
    }
    """Styles for each log level."""
    GRADIENTS: Dict[str, list[str]] = {
        "TRACE": ["#888888", "#aaaaaa", "#ffffff"],
        "DEBUG": ["#0F8C8C", "#19cfcf", "#00ffff"],
        "INFO": ["#1b83d3", "#00afff", "#54d1ff"],
        "SUCCESS": ["#00ff90", "#00ff00", "#afff00"],
        "WARNING": ["#ffaa00", "#ffcc00", "#ffff00"],
        "ERROR": ["#ff7700", "#ff5500", "#ff3300"],
        "CRITICAL": ["#ff0000", "#ff005f", "#ff009f"],
    }
    """Gradients for log level titles."""
    MSG_COLORS: Dict[str, list[str]] = {
        "TRACE": ["#eeeeee", "#dddddd", "#bbbbbb"],
        "INFO": ["#a4e7ff", "#72d3ff", "#52daff"],
        "SUCCESS": ["#d3ffd3", "#a9ffa9", "#64ff64"],
        "WARNING": ["#ffeb9b", "#ffe26e", "#ffc041"],
        "ERROR": ["#ffc59c", "#ffaa6e", "#FF4E3A"],
        "CRITICAL": ["#ffaaaa", "#FF6FA4", "#FF49C2"],
    }
    """Gradients for log message text."""

    def __init__(
        self,
        console: Optional[Console] = None,
        track_run: bool = TRACK_RUN,
        run: Optional[int] = None,
        padding: Tuple[int, int] = (1, 2),
        expand: bool = False,
        record: bool = False,
    ) -> None:
        """
        Args:
            console (Optional[Console]): An optional Rich console.
            track_run (bool): Whether to track runs.
            run (Optional[int]): The current run number. If None, it is read from the run file.
        """
        if track_run:
            if run is None:
                try:
                    run = read_run_from_file()
                except FileNotFoundError:
                    run = setup()
            self.run = run
        else:
            self.run = None
        self.console: Console = console or _console
        if record:
            self.console.record = True
            self.record = True
        else:
            self.console.record = False
            self.record = False
        self.padding: Tuple[int, int] = padding or (1, 2)
        self.expand: bool = expand

    def __call__(self, message: loguru.Message) -> None:
        """
        Print a loguru.Message to the Rich console as a styled panel.

        Args:
            message (Message): The loguru message to print.
        """
        record = message.record
        panel = self._build_panel(record, self.run)
        self.console.print(panel)

    def _build_panel(self, record: loguru.Record, run: Optional[int] = None) -> Panel:
        """
        Helper method to build a Rich Panel for a log record.

        Args:
            record (Record): The log record.
            run (Optional[int]): The current run count.

        Returns:
            Panel: A Rich Panel containing the formatted log message.
        """
        _level: str = record["level"].name
        colors = self.GRADIENTS.get(_level, [])
        style = self.LEVEL_STYLES.get(_level, Style())
        msg_style = self.MSG_COLORS.get(
            _level,
            [
                "#eeeeee",
                "#aaaaaa",
                "#888888",
            ],
        )
        # Title with gradient and highlighted separators.
        _file: str = record["file"].name
        line_str: str = str(record["line"])
        _line: str = f"Line {line_str}"
        title: Text = Text(
            f" {_level:^10} | {_file:^14} | {_line:^14} ",
            colors=colors,
        )
        title.stylize(Style(reverse=True))
        title.highlight_words([_level, _file, _line], style="bold on white")

        # Subtitle with run count and formatted time.
        subtitle_run_elements: list[RichText] = [
            RichText(f"Run {run}"),
            RichText(" | "),
        ]
        subtitle_elements: list[RichText] = [
            RichText(record["time"].strftime("%h:%M:%S.%f")[:-3]),
            RichText(record["time"].strftime(" %p")),
        ]
        if run is not None:
            subtitle_elements = subtitle_run_elements + subtitle_elements

        subtitle: RichText = RichText.assemble(*subtitle_elements)
        subtitle.highlight_words(":", style="dim #aaaaaa")

        # Message text with gradient.
        message_text: Text = Text(record["message"], colors=msg_style)
        return Panel(
            message_text,
            title=title,
            title_align="left",
            subtitle=subtitle,
            subtitle_align="right",
            border_style=style + Style(bold=True),
            padding=self.padding,
            expand=self.expand,
        )


_RUN_HEADER_PATTERN = re.compile(r"Run (\d+) Completed")


def on_exit() -> None:
    """
    At exit, increment the run count, add a header to the run’s log,
    and trim the trace log to the last three runs.
    """
    log = get_logger()
    run = increment_run_and_write_to_file()
    if VERBOSE:
        log.info(f"Run {run} Completed")
    with open("logs/run.txt", "r", encoding="utf-8") as run_file:
        run = int(run_file.read())
    trace_log_path = LOGS_DIR / "trace.log"

    bar_str: str = f"{str('━'*15)}"
    with open(trace_log_path, "a", encoding="utf-8") as trace_log_file:
        header = f"\n\n{bar_str} Run {run} {bar_str}\n"
        trace_log_file.write(header)
    # Process the log file line by line to build segments.





atexit.register(on_exit)

for _export_name in __all__:
    if _export_name not in globals():
        raise AttributeError(
            f"Export '{_export_name}' is listed in __all__ but is not defined in rich_logger.logger."
        )
del _export_name

if __name__ == "__main__":
    _console = get_console()
    _logger: loguru.Logger = get_logger(console=_console, level="TRACE")
    _console.clear()
    _console.line(2)
    _console.print(
        Rule(
            "Loguru Logger using rich.console.Console",
        )
    )
    _logger.trace(
        "This is a loguru.Message logged to a rich.console.Console at Level.TRACE"
    )
    _logger.debug(
        "This is a loguru.Message logged to a rich.console.Console at Level.DEBUG"
    )
    _logger.info(
        "This is a loguru.Message logged to a rich.console.Console at Level.INFO"
    )
    _logger.success(
        "This is a loguru.Message logged to a rich.console.Console at Level.SUCCESS"
    )
    _logger.warning(
        "This is a loguru.Message logged to a rich.console.Console at Level.WARNING"
    )
    _logger.error(
        "This is a loguru.Message logged to a rich.console.Console at Level.ERROR"
    )
    _logger.critical(
        "This is a loguru.Message logged to a rich.console.Console at Level.CRITICAL"
    )

    sys.exit(0)
