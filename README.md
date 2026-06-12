# Rich Logger

Rich Logger is a drop-in wrapper around [`loguru.logger`](https://github.com/Delgan/loguru) that renders console logs as Rich panels while preserving Loguru's sink system.

- `from rich_logger import logger` is the canonical API.
- `from rich_logger import log` remains as a compatibility alias.
- Rich renderables are shown as renderables in the default console panel sink.
- Files, JSON logs, callable sinks, async sinks, and other Loguru sinks receive plain text messages.

## Installation

```sh
pip install rich-logger
```

For local development:

```sh
python -m pip install -e .
```

## Quick Start

```python
from rich_logger import logger


def main() -> None:
    """Run a small logging example."""
    logger.info("Hello, colourful world!")
    logger.success("All systems go")


if __name__ == "__main__":
    main()
```

By default, Rich Logger removes Loguru's default stderr sink and adds a Rich console sink that renders each message in a panel. The panel includes the level, module/function, and timestamp.

## Rich Renderables

Any object that implements Rich's render protocol can be logged directly.

```python
from rich.panel import Panel
from rich.table import Table
from rich_logger import logger

logger.info(Panel("Rendered inside the log panel", title="Rich object"))

table = Table("Name", "Role")
table.add_row("Ada", "Engineer")
logger.info(table)
```

The default Rich sink receives the original object. Other Loguru sinks receive plain text rendered from that object.

## Loguru Sinks

Use `logger.add()` exactly as you would with Loguru.

```python
from pathlib import Path

from rich.panel import Panel
from rich_logger import logger

path = Path("app.log")
handler_id = logger.add(path, format="{level} | {message}", level="INFO")

logger.info(Panel("This appears as plain text in app.log", title="File sink"))
logger.remove(handler_id)
```

Callable, async, file-like, standard-library handler, serialized, rotation, retention, and compression sinks are forwarded to Loguru.

## Configuration

Use `setup_logger()` when you want to replace the default console, level, padding, expansion, or plain-text render width.

```python
from rich.console import Console
from rich_logger import RichLoggerConfig, setup_logger

console = Console(width=120)
config = RichLoggerConfig(
    console=console,
    level="DEBUG",
    panel_padding=(1, 2),
    panel_expand=True,
    render_width=100,
)

logger = setup_logger(config)
logger.debug("Configured logger")
```

For a temporary logger without configuring the default Rich sink:

```python
from rich_logger import get_logger

logger = get_logger(configure_default_sink=False)
logger.remove()
handler_id = logger.add("plain.log", format="{message}")
logger.info("Only written to plain.log")
logger.remove(handler_id)
```

## Chaining

`bind()`, `opt()`, and `patch()` return `RichLogger` instances, so Rich renderable support survives chained Loguru calls.

```python
from rich.panel import Panel
from rich_logger import logger

logger.bind(request_id="abc").opt(depth=0).info(Panel("Still rendered"))
```

## Public API

- `logger`: canonical Rich Logger instance.
- `log`: alias to `logger`.
- `RichLogger`: Loguru-compatible wrapper class.
- `RichSink`: callable Loguru sink that renders records as Rich panels.
- `RichLoggerConfig`: typed configuration object.
- `setup_logger()`: configure and return the shared logger.
- `get_logger()`: build a configured logger wrapper.
- `get_console()`: get or replace the shared Rich console.
- `render_plain()`: convert a Rich renderable to plain text.

## Development

```sh
.venv/bin/python -m pytest
```

The project currently targets Python 3.14 and depends on Loguru 0.7.3 and Rich 15.0.0.
