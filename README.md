# Rich Logger

Rich Logger is a colourful, batteries-included wrapper around [`loguru`](https://github.com/Delgan/loguru) that pairs vibrant Rich-rendered output with sensible defaults for long-running scripts, batch jobs, and tooling.

- Drop-in replacement for `loguru.logger` with Rich panels, gradients, and progress bars.
- Automatically captures plain-text logs alongside the colourful console output.
- Tracks successive runs and annotates log files with run metadata.
- Easily configurable via a Python API or `RICH_LOGGER_*` environment variables.

## Installation

### Install via [uv](https://uv.run)(Recommended):
```sh
uv add rich_logger
```

### Install via pip:
```sh
pip install rich_logger
```

 ### If you are developing locally, install in editable mode:

```sh
uv pip install -e .
```

## Quick Start

```python
# main.py
from rich_logger import log

def main() -> None:
    log.info("Hello, colourful world!")
    log.success("All systems go")

if __name__ == "__main__":
    main()
```

By default, the package:

- creates a Rich-powered console logger;
- writes colour-stripped messages to `logs/trace.log`;
- tracks run numbers in `logs/run.txt` and displays them in panel subtitles.

## Advanced Usage

### Custom configuration

Use `rich_logger.LoggerConfig` to customise behaviour programmatically:

```python
from rich_logger import LoggerConfig, setup_logger

config = LoggerConfig(
    level="DEBUG",
    verbose=True,
    padding=(1, 4),
    additional_sinks=[
        {"sink": "logs/errors.log", "level": "ERROR", "format": "{time} | {message}"},
    ],
)

log = setup_logger(config)
log.debug("Initialised with custom configuration")
```

You can also override configuration via environment variables. Prefix every option with `RICH_LOGGER_` (custom prefixes are supported when instantiating `LoggerConfig` manually):

| Variable | Description | Default |
| --- | --- | --- |
| `RICH_LOGGER_LEVEL` | Log level string or integer (`TRACE`, `INFO`, `30`, …) | `INFO` |
| `RICH_LOGGER_VERBOSE` | Enable verbose mode (`true/false`) | `false` |
| `RICH_LOGGER_TRACK_RUN` | Track and persist run counts (`true/false`) | `true` |
| `RICH_LOGGER_RECORD` | Record console output for post-processing (`true/false`) | `false` |
| `RICH_LOGGER_SHOW_LOCALS` | Display locals in tracebacks (`true/false`) | `false` |
| `RICH_LOGGER_PADDING` | Panel padding as `"top bottom"` or `"top,bottom"` | `1 2` |
| `RICH_LOGGER_EXPAND` | Expand panels to console width (`true/false`) | `true` |
| `RICH_LOGGER_LOGS_DIR` | Directory for trace logs and run file | project `logs/` |
| `RICH_LOGGER_RUN_FILE` | Override the run counter file path | `<logs>/run.txt` |
| `RICH_LOGGER_ADDITIONAL_SINKS` | JSON list/dict describing extra Loguru handlers | `[]` |

Example (`.env` or shell):

```bash
export RICH_LOGGER_LEVEL=DEBUG
export RICH_LOGGER_ADDITIONAL_SINKS='[{"sink": "logs/warnings.log", "level": "WARNING"}]'
python main.py
```

### Direct API access

All of the lower-level building blocks live in `rich_logger.core.logger`. Import them directly if you need the bespoke components:

- `get_console()` – obtain the shared Rich console.
- `get_progress()` – create a Rich progress bar wired to the logger console.
- `get_logger()` – build a configured Loguru logger with custom sinks.
- `trace_sink()` – retrieve the configuration dict for the trace log handler.

```python
from rich_logger.core.logger import get_console, get_progress

console = get_console()
with get_progress(console) as progress:
    task = progress.add_task("Processing", total=5)
    for _ in range(5):
        # do work
        progress.advance(task)
```

## Project Structure

- `rich_logger/core` contains the implementation, including configuration helpers and the Rich sink.
- The top-level `logger.py` module re-exports the core functionality for backwards compatibility (e.g. `import logger`).
- `logs/` houses generated run counts and trace files (created at runtime).

## Contributing

1. Fork / clone the repository.
2. Install dependencies with `pip install -e .`.
3. Run the test suite (add tests for new behaviour).
4. Submit a pull request describing your changes and how to verify them.

## License

This project is released under the MIT License. See `LICENSE` for details.
