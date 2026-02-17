"""Workflow tools — thin async wrappers around workflow orchestration planners."""

from __future__ import annotations

from typing import Any


async def odoo_setup_business(
    blueprint_name: str,
    company_name: str,
    db_name: str,
    locations: int = 1,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Set up a complete business from an industry blueprint."""
    from odooforge.workflows.setup_business import setup_business
    return setup_business(blueprint_name, company_name, db_name, locations, dry_run)


async def odoo_create_feature(
    feature_name: str,
    target_model: str,
    fields: list[dict[str, Any]],
    db_name: str,
    add_to_views: bool = True,
    automation: dict[str, Any] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a complete feature in one call."""
    from odooforge.workflows.create_feature import create_feature
    return create_feature(
        feature_name, target_model, fields, db_name, add_to_views, automation, dry_run,
    )


async def odoo_create_dashboard(
    dashboard_name: str,
    metrics: list[dict[str, Any]],
    db_name: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a management dashboard."""
    from odooforge.workflows.create_dashboard import create_dashboard
    return create_dashboard(dashboard_name, metrics, db_name, dry_run)


async def odoo_setup_integration(
    integration_type: str,
    provider: str,
    db_name: str,
    settings: dict[str, Any],
    dry_run: bool = True,
) -> dict[str, Any]:
    """Configure an external integration (email, payment, shipping)."""
    from odooforge.workflows.setup_integration import setup_integration
    return setup_integration(integration_type, provider, db_name, settings, dry_run)
