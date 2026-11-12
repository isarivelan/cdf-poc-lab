"""Cognite Data Fusion access for cognite-sdk 8.23+."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from maintenance_investigator.exceptions import (
    CdfAuthenticationError,
    IngestionError,
    ResourceNotFoundError,
)
from maintenance_investigator.settings import Settings

logger = logging.getLogger(__name__)

_TRANSIENT = {408, 429, 500, 502, 503, 504}


def build_client(settings: Settings) -> Any:
    """Create a CogniteClient from settings. The secret is not logged."""
    try:
        from cognite.client import ClientConfig, CogniteClient
        from cognite.client.credentials import OAuthClientCredentials
    except ImportError as exc:
        raise IngestionError(
            "cognite-sdk is not installed.",
            likely_cause="The CDF extra is missing from the environment.",
            action='Install the project with pip install -e ".[dev]".',
        ) from exc
    credentials = OAuthClientCredentials(
        token_url=settings.cdf_token_url,
        client_id=settings.cdf_client_id,
        client_secret=settings.cdf_client_secret,
        scopes=settings.scopes(),
    )
    config = ClientConfig(
        client_name="cdf-intelligent-maintenance-investigator",
        project=settings.cdf_project,
        base_url=settings.base_url(),
        credentials=credentials,
        timeout=60,
    )
    return CogniteClient(config)


def probe_connection(settings: Settings) -> tuple[str, str]:
    """Check that a token can be acquired. The token is not returned or logged."""
    try:
        client = build_client(settings)
        header, token = client.config.credentials.authorization_header()
        if header != "Authorization" or not token:
            raise CdfAuthenticationError(
                "CDF did not return an access token.",
                likely_cause="The token endpoint response was empty.",
                action="Check CDF_TOKEN_URL, CDF_CLIENT_ID, CDF_CLIENT_SECRET, and CDF_SCOPES.",
            )
        return "ok", "CDF authentication succeeded."
    except Exception as exc:
        if isinstance(exc, CdfAuthenticationError):
            return "error", str(exc)
        text = str(exc)
        if settings.cdf_client_secret and settings.cdf_client_secret in text:
            text = "Authentication failed. The client secret was removed from this message."
        return (
            "error",
            "CDF authentication failed. Likely cause: the project, cluster, or client credentials "
            f"were rejected. Action: verify the development .env values. Detail: {text[:300]}",
        )


def _call(operation: Any) -> Any:
    from cognite.client.exceptions import CogniteAPIError, CogniteAuthError

    try:
        return operation()
    except CogniteAuthError as exc:
        raise CdfAuthenticationError(
            "CDF rejected the credentials.",
            likely_cause="The token request failed.",
            action="Check the client credentials and scopes. The secret was not logged.",
        ) from exc
    except CogniteAPIError as exc:
        status = getattr(exc, "code", None)
        if status in _TRANSIENT:
            try:
                return operation()
            except CogniteAPIError as retry_exc:
                raise IngestionError(
                    "CDF did not complete the request after a retry.",
                    likely_cause=f"HTTP {getattr(retry_exc, 'code', 'unknown')}.",
                    action="Wait and retry the script. Do not switch to a production project.",
                ) from retry_exc
        raise IngestionError(
            "CDF rejected the request.",
            likely_cause=f"HTTP {status}.",
            action="Check the data set, space, and external ids in the development project.",
        ) from exc


class CdfRepository:
    """Write and read the demo model. Methods are idempotent upserts."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = build_client(settings)

    def ensure_dataset(self) -> int:
        """Return the data set id, creating it when absent."""
        from cognite.client.data_classes import DataSetWrite

        external_id = self.settings.cdf_data_set_external_id

        def _retrieve() -> Any:
            return self.client.data_sets.retrieve(external_id=external_id)

        existing = _call(_retrieve)
        if existing is not None:
            return int(existing.id)
        created = _call(
            lambda: self.client.data_sets.create(
                DataSetWrite(
                    external_id=external_id,
                    name="CDF Maintenance Investigator",
                    description="Synthetic Pump P-101 demonstration data set.",
                )
            )
        )
        return int(created.id)

    def upsert_time_series(self, rows: list[dict[str, str]], data_set_id: int) -> int:
        """Create or update time series metadata."""
        from cognite.client.data_classes import TimeSeriesWrite

        writes = [
            TimeSeriesWrite(
                external_id=row["external_id"],
                name=row["name"],
                unit=row["unit"],
                description=row.get("description", ""),
                data_set_id=data_set_id,
                metadata={"equipment": row.get("equipment", "")},
            )
            for row in rows
        ]
        _call(lambda: self.client.time_series.upsert(writes, mode="patch"))
        return len(writes)

    def insert_datapoints(self, frame: pd.DataFrame, batch_size: int = 5_000) -> int:
        """Insert numeric datapoints in batches. Timestamps are UTC milliseconds."""
        stamped = pd.to_datetime(frame["timestamp"], utc=True)
        total = 0
        for external_id, group in frame.groupby("sensor_external_id"):
            times = stamped.loc[group.index]
            points = [
                (int(stamp.timestamp() * 1000), float(value))
                for stamp, value in zip(times, group["value"], strict=True)
            ]
            for start in range(0, len(points), batch_size):
                batch = points[start : start + batch_size]
                _call(
                    lambda batch=batch, external_id=external_id: (
                        self.client.time_series.data.insert_multiple(
                            [{"external_id": external_id, "datapoints": batch}]
                        )
                    )
                )
                total += len(batch)
        return total

    def apply_instances(self, nodes: list[Any], edges: list[Any] | None = None) -> None:
        """Upsert data-model nodes and edges."""
        _call(
            lambda: self.client.data_modeling.instances.apply(
                nodes=nodes or None,
                edges=edges or None,
                auto_create_direct_relations=True,
            )
        )

    def list_nodes(self, view_external_id: str) -> list[Any]:
        """List nodes for one view. The SDK paginates when limit is None."""
        from cognite.client.data_classes.data_modeling import ViewId

        view = ViewId(self.settings.cdf_space, view_external_id, "v1")
        try:
            result = _call(
                lambda: self.client.data_modeling.instances.list(
                    instance_type="node",
                    sources=[view],
                    space=self.settings.cdf_instance_space,
                    limit=None,
                )
            )
        except IngestionError as exc:
            raise ResourceNotFoundError(
                f"Could not list {view_external_id} nodes.",
                likely_cause="The view or space has not been deployed.",
                action="Deploy the Toolkit module to development, then ingest master data.",
            ) from exc
        return list(result)

    def delete_time_series(self, external_ids: list[str]) -> None:
        """Delete demo time series by external id."""
        _call(
            lambda: self.client.time_series.delete(
                external_id=external_ids, ignore_unknown_ids=True
            )
        )
