"""One-off emitter for Toolkit 0.9 data-model YAML. Not part of the runtime."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "maintenance_investigator"
SPACE = "cdf_maintenance_demo"
INSTANCE = "cdf_maintenance_demo_instances"
DATASET = "cdf-maintenance-investigator-demo"

CONTAINERS: dict[str, list[tuple[str, str, bool]]] = {
    "Site": [("name", "text", False), ("description", "text", True)],
    "FunctionalLocation": [
        ("name", "text", False),
        ("description", "text", True),
        ("parent", "direct", True),
    ],
    "Equipment": [
        ("name", "text", False),
        ("description", "text", True),
        ("equipmentType", "text", True),
        ("manufacturer", "text", True),
        ("model", "text", True),
        ("serialNumber", "text", True),
        ("installationDate", "date", True),
        ("criticality", "text", True),
        ("status", "text", True),
        ("functionalLocation", "direct", True),
    ],
    "Sensor": [
        ("name", "text", False),
        ("unit", "text", True),
        ("measurementType", "text", True),
        ("timeSeriesExternalId", "text", True),
        ("equipment", "direct", True),
    ],
    "WorkOrder": [
        ("title", "text", False),
        ("description", "text", True),
        ("workType", "text", True),
        ("priority", "text", True),
        ("status", "text", True),
        ("openedTime", "timestamp", True),
        ("completedTime", "timestamp", True),
        ("failureMode", "text", True),
        ("cause", "text", True),
        ("correctiveAction", "text", True),
        ("equipment", "direct", True),
        ("relatedIncident", "direct", True),
    ],
    "TechnicalDocument": [
        ("title", "text", False),
        ("documentType", "text", True),
        ("revision", "text", True),
        ("effectiveDate", "date", True),
        ("sectionIndex", "json", True),
        ("equipment", "direct", True),
    ],
    "MaintenanceIncident": [
        ("title", "text", False),
        ("startTime", "timestamp", True),
        ("endTime", "timestamp", True),
        ("severity", "text", True),
        ("status", "text", True),
        ("detectionRule", "text", True),
        ("healthScore", "float64", True),
        ("summary", "text", True),
        ("equipment", "direct", True),
    ],
    "Investigation": [
        ("generatedTime", "timestamp", True),
        ("confidence", "float64", True),
        ("modelInformation", "text", True),
        ("observedFacts", "json", True),
        ("evidence", "json", True),
        ("hypotheses", "json", True),
        ("recommendedActions", "json", True),
        ("safetyNotes", "json", True),
        ("incident", "direct", True),
        ("equipment", "direct", True),
    ],
}


def prop(name: str, kind: str, nullable: bool) -> str:
    nullable_text = "true" if nullable else "false"
    return f"    {name}:\n      nullable: {nullable_text}\n      type:\n        type: {kind}\n"


def main() -> None:
    modeling = MODULE / "data_modeling"
    modeling.mkdir(parents=True, exist_ok=True)
    (modeling / "spaces.Space.yaml").write_text(
        "\n".join(
            [
                f"- space: {SPACE}",
                "  name: Maintenance investigator schema",
                "  description: Schema space for the synthetic Pump P-101 demonstration.",
                f"- space: {INSTANCE}",
                "  name: Maintenance investigator instances",
                "  description: Instance space for synthetic demo nodes.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    containers = ["# Generated for cognite-toolkit 0.9. Containers use direct relations for links."]
    views = ["# Views map one-to-one onto the demo containers."]
    for external_id, fields in CONTAINERS.items():
        containers.append(f"- space: {SPACE}")
        containers.append(f"  externalId: {external_id}")
        containers.append(f"  name: {external_id}")
        containers.append("  usedFor: node")
        containers.append("  properties:")
        containers.append(
            "".join(prop(name, kind, nullable) for name, kind, nullable in fields).rstrip()
        )
        views.append(f"- space: {SPACE}")
        views.append(f"  externalId: {external_id}")
        views.append("  version: v1")
        views.append(f"  name: {external_id}")
        views.append("  properties:")
        for name, _kind, _nullable in fields:
            views.append(f"    {name}:")
            views.append("      container:")
            views.append("        type: container")
            views.append(f"        space: {SPACE}")
            views.append(f"        externalId: {external_id}")
            views.append(f"      containerPropertyIdentifier: {name}")
    (modeling / "model.Container.yaml").write_text("\n".join(containers) + "\n", encoding="utf-8")
    (modeling / "model.View.yaml").write_text("\n".join(views) + "\n", encoding="utf-8")
    view_refs = []
    for external_id in CONTAINERS:
        view_refs.extend(
            [
                "  - type: view",
                f"    space: {SPACE}",
                f"    externalId: {external_id}",
                "    version: v1",
            ]
        )
    (modeling / "MaintenanceInvestigation.DataModel.yaml").write_text(
        "\n".join(
            [
                f"space: {SPACE}",
                "externalId: MaintenanceInvestigation",
                "version: v1",
                "name: Maintenance investigation",
                "description: Synthetic maintenance investigation model for Pump P-101.",
                "views:",
                *view_refs,
                "",
            ]
        ),
        encoding="utf-8",
    )
    (MODULE / "data_sets").mkdir(exist_ok=True)
    (MODULE / "data_sets" / "demo.DataSet.yaml").write_text(
        "\n".join(
            [
                f"externalId: {DATASET}",
                "name: Maintenance investigator demo",
                "description: Synthetic Pump P-101 data. Development use only.",
                "writeProtected: false",
                "",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
