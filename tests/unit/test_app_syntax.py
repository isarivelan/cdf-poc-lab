"""Parse Streamlit modules without starting a server."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_application_modules_parse(repo_root: Path) -> None:
    for path in (repo_root / "app").rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
