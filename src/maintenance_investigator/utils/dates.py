"""UTC timestamps and ISO-8601 serialization."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd


def to_utc(value: Any) -> datetime:
    """Convert a datetime-like value to timezone-aware UTC."""
    if isinstance(value, datetime):
        stamp = value
    else:
        stamp = pd.Timestamp(value).to_pydatetime()
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    return stamp.astimezone(UTC)


def to_iso(value: Any) -> str:
    """Serialize a timestamp as UTC ISO-8601 with a Z suffix."""
    return to_utc(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_millis(value: Any) -> int:
    """Convert a timestamp to Unix milliseconds."""
    return int(to_utc(value).timestamp() * 1000)
