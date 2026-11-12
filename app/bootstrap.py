"""Shared path setup for Streamlit pages."""

from __future__ import annotations

import sys
from pathlib import Path


def bootstrap(start_file: str) -> Path:
    """Add the repository and src directory to sys.path and return the root."""
    start = Path(start_file).resolve()
    root = start
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            root = candidate
            break
    src = root / "src"
    for path in (str(root), str(src)):
        if path not in sys.path:
            sys.path.insert(0, path)
    return root
