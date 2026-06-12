"""Smoke tests for bundled example scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_example_scripts_run_from_checkout(tmp_path: Path) -> None:
    """Run example scripts directly from the repository checkout."""
    root = Path(__file__).resolve().parents[1]
    scripts = [
        root / "scripts" / "quickstart.py",
        root / "scripts" / "example_dynamic_config.py",
    ]

    for script in scripts:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=tmp_path,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
