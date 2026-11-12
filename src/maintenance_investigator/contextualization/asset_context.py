"""Assemble the asset view used by an investigation."""

from __future__ import annotations

from maintenance_investigator.models.asset import Asset, AssetContext


def build_asset_context(
    assets: list[Asset], equipment_id: str, related_ids: list[str]
) -> AssetContext:
    """Collect the equipment node, its location, the site, and configured relatives."""
    by_id = {asset.external_id: asset for asset in assets}
    equipment = by_id[equipment_id]
    location = by_id.get(equipment.functional_location) or by_id.get(equipment.parent_external_id)
    site = next((asset for asset in assets if asset.entity_type == "site"), None)
    related = [by_id[item] for item in related_ids if item in by_id and item != equipment_id]
    return AssetContext(
        equipment=equipment,
        functional_location=location,
        site=site,
        related_equipment=related,
    )
