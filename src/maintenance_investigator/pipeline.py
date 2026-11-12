"""End-to-end local investigation pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from maintenance_investigator.clients.ai_client import MockInvestigator, OpenAICompatibleProvider
from maintenance_investigator.clients.local_repository import LocalRepository
from maintenance_investigator.constants import DECISION_SUPPORT_NOTICE, PRIMARY_EQUIPMENT
from maintenance_investigator.contextualization.document_linking import parse_manual
from maintenance_investigator.detection.rules import load_rules
from maintenance_investigator.exceptions import OperationalSafetyError
from maintenance_investigator.investigation.context_builder import ContextPackage, build_context
from maintenance_investigator.investigation.investigator import Investigator
from maintenance_investigator.logging_config import configure_logging, log_stage, new_correlation_id
from maintenance_investigator.models.incident import MaintenanceIncident
from maintenance_investigator.models.investigation import InvestigationRecord
from maintenance_investigator.paths import config_dir, load_yaml
from maintenance_investigator.services.data_quality_service import data_quality_report
from maintenance_investigator.services.health_score_service import current_health
from maintenance_investigator.services.incident_service import (
    classic_event_payload,
    detect_incidents,
)
from maintenance_investigator.settings import Settings, load_settings
from maintenance_investigator.synthetic.catalog import assets, sensors, work_orders
from maintenance_investigator.utils.dates import to_iso
from maintenance_investigator.utils.identifiers import investigation_external_id

logger = logging.getLogger(__name__)


class DisabledWorkOrderGateway:
    """Extension point that refuses to create a real work order."""

    def submit(self, draft: dict[str, object]) -> str:
        """Reject automatic work-order creation."""
        del draft
        raise OperationalSafetyError(
            "This POC does not create work orders.",
            likely_cause="Automatic write-back is disabled.",
            action="A person must create the work order after reviewing the evidence.",
        )


class LocalNotificationSink:
    """Store a notification payload and do not call an external system."""

    def __init__(self, repository: LocalRepository) -> None:
        self.repository = repository

    def send(self, payload: dict[str, object]) -> None:
        """Persist the payload locally."""
        self.repository.save_notification(payload)


@dataclass
class PipelineResult:
    """Outputs of one local pipeline run."""

    correlation_id: str
    incidents: list[MaintenanceIncident]
    investigations: list[InvestigationRecord]
    health_score: float
    quality: dict[str, object]
    notification: dict[str, object] | None = None
    contexts: list[ContextPackage] = field(default_factory=list)
    classic_events: list[dict[str, object]] = field(default_factory=list)


def _provider(settings: Settings) -> MockInvestigator | OpenAICompatibleProvider:
    if settings.ai_provider.value == "openai_compatible":
        return OpenAICompatibleProvider(
            endpoint=settings.ai_endpoint,
            api_key=settings.ai_api_key,
            model=settings.ai_model,
        )
    return MockInvestigator()


def _notification(
    incident: MaintenanceIncident, record: InvestigationRecord, link: str
) -> dict[str, object]:
    action = (
        record.response.recommended_actions[0].action if record.response.recommended_actions else ""
    )
    return {
        "title": f"{incident.severity.title()} maintenance incident: Pump P-101",
        "severity": incident.severity,
        "health_score": incident.health_score,
        "summary": record.response.investigation_summary,
        "recommended_action": action,
        "incident_external_id": incident.external_id,
        "application_link": link,
        "decision_support": DECISION_SUPPORT_NOTICE,
    }


def run_local_pipeline(
    root: Path | None = None, settings: Settings | None = None
) -> PipelineResult:
    """Run detection, context, and investigation against local files."""
    active = settings or load_settings(environ={}, repo_root=root) if root else load_settings()
    if root is not None:
        active.repo_root = root
    configure_logging(active.log_level)
    correlation = new_correlation_id()
    repository = LocalRepository(active.repo_root)
    app_config = load_yaml(config_dir(active.repo_root) / "app.yaml")
    rules = load_rules(config_dir(active.repo_root) / "anomaly_rules.yaml")
    recommendations = load_yaml(config_dir(active.repo_root) / "recommendations.yaml")
    with log_stage(logger, "read_sensor_data", asset_external_id=PRIMARY_EQUIPMENT):
        frame = repository.load_sensor_frame()
    catalog_assets = assets()
    catalog_sensors = sensors()
    catalog_orders = work_orders()
    document = parse_manual(repository.load_manual_text())
    repository.save_assets(catalog_assets)
    repository.save_sensors(catalog_sensors)
    repository.save_work_orders(catalog_orders)
    repository.save_documents([document])
    with log_stage(logger, "detect", asset_external_id=PRIMARY_EQUIPMENT, record_count=len(frame)):
        wide, incidents, _statistical = detect_incidents(frame, app_config=app_config, rules=rules)
    repository.save_incidents(incidents)
    investigator = Investigator(_provider(active), recommendations)
    records: list[InvestigationRecord] = []
    contexts: list[ContextPackage] = []
    for incident in incidents:
        with log_stage(
            logger,
            "investigate",
            incident_external_id=incident.external_id,
            asset_external_id=incident.equipment,
        ):
            context = build_context(
                incident,
                assets=catalog_assets,
                work_orders=catalog_orders,
                document=document,
                wide=wide,
                app_config=app_config,
                related_ids=list(app_config["related_equipment"]),
            )
            response = investigator.run(context)
        confidence = max((item.confidence for item in response.hypotheses), default=0.0)
        record = InvestigationRecord(
            external_id=investigation_external_id(incident.external_id),
            incident=incident.external_id,
            equipment=incident.equipment,
            generated_time=to_iso(datetime.now(UTC)),
            confidence=confidence,
            model_information=investigator.provider.name,
            response=response,
        )
        records.append(record)
        contexts.append(context)
        incident.investigation_status = "completed"
    repository.save_incidents(incidents)
    repository.save_investigations(records)
    notification = None
    critical = [item for item in incidents if item.severity == "critical"]
    if critical and records:
        match = next(record for record in records if record.incident == critical[-1].external_id)
        notification = _notification(critical[-1], match, "http://localhost:8501")
        LocalNotificationSink(repository).send(notification)
    quality = data_quality_report(
        frame,
        assets=catalog_assets,
        sensors=catalog_sensors,
        work_orders=catalog_orders,
        documents=[document],
        incidents=incidents,
        ranges=app_config["quality_ranges"],
    )
    events = [classic_event_payload(incident) for incident in incidents]
    return PipelineResult(
        correlation_id=correlation,
        incidents=incidents,
        investigations=records,
        health_score=current_health(wide, app_config),
        quality=quality,
        notification=notification,
        contexts=contexts,
        classic_events=events,
    )
