"""Repository paths and YAML loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from maintenance_investigator.exceptions import ConfigurationError


def find_repo_root(start: Path | None = None) -> Path:
    """Return the directory that contains pyproject.toml and config/."""
    origin = (start or Path(__file__)).resolve()
    for candidate in (origin, *origin.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "config").is_dir():
            return candidate
    raise ConfigurationError(
        "Could not locate the project root.",
        likely_cause="pyproject.toml or config/ is missing.",
        action="Run commands from the repository root.",
    )


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping."""
    if not path.is_file():
        raise ConfigurationError(
            f"Configuration file {path.name} was not found.",
            likely_cause=f"Expected a file at {path}.",
            action="Restore the file from the repository.",
        )
    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ConfigurationError(
            f"Configuration file {path.name} is not a mapping.",
            likely_cause="The YAML root is empty or a list.",
            action="Restore the mapping structure from the repository.",
        )
    return loaded


def config_dir(root: Path | None = None) -> Path:
    """Return the config directory."""
    return (root or find_repo_root()) / "config"
