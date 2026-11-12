"""Structured logging with a correlation id and processing stage."""

from __future__ import annotations

import logging
import logging.config
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from maintenance_investigator.paths import config_dir, find_repo_root, load_yaml

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")
_stage: ContextVar[str] = ContextVar("stage", default="-")


class _ContextFilter(logging.Filter):
    """Attach correlation fields without reading the log message for secrets."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = _correlation_id.get()
        record.stage = _stage.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once from config/logging.yaml."""
    root_logger = logging.getLogger()
    if getattr(root_logger, "_maintenance_configured", False):
        root_logger.setLevel(level)
        return
    path = config_dir(find_repo_root()) / "logging.yaml"
    loaded = load_yaml(path)
    logging.config.dictConfig(loaded)
    context_filter = _ContextFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(context_filter)
    logging.getLogger().setLevel(level)
    root_logger._maintenance_configured = True  # type: ignore[attr-defined]


def new_correlation_id() -> str:
    """Create a short correlation id for one pipeline run."""
    value = uuid.uuid4().hex[:12]
    _correlation_id.set(value)
    return value


@contextmanager
def log_stage(
    logger: logging.Logger,
    stage: str,
    *,
    incident_external_id: str = "",
    asset_external_id: str = "",
    record_count: int | None = None,
) -> Iterator[None]:
    """Log the start and end of a stage, including duration and status."""
    token = _stage.set(stage)
    started = time.perf_counter()
    logger.info(
        "stage_started incident=%s asset=%s records=%s",
        incident_external_id or "-",
        asset_external_id or "-",
        "-" if record_count is None else record_count,
    )
    try:
        yield
    except Exception:
        logger.error(
            "stage_failed incident=%s asset=%s duration_ms=%s",
            incident_external_id or "-",
            asset_external_id or "-",
            int((time.perf_counter() - started) * 1000),
        )
        raise
    else:
        logger.info(
            "stage_completed incident=%s asset=%s records=%s duration_ms=%s status=success",
            incident_external_id or "-",
            asset_external_id or "-",
            "-" if record_count is None else record_count,
            int((time.perf_counter() - started) * 1000),
        )
    finally:
        _stage.reset(token)
