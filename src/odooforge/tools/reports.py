"""QWeb report tools — list, get template, modify, preview, reset, layout."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC
from odooforge.utils.qweb_builder import build_qweb_inherit_xml

logger = logging.getLogger(__name__)


async def odoo_report_list(
    rpc: OdooRPC,
    db_name: str,
    model: str | None = None,
) -> dict[str, Any]:
    """List all available reports, optionally filtered by model.

    Args:
        model: Filter reports for this model (e.g., "sale.order").
    """
    domain: list = []
    if model:
        domain.append(("model", "=", model))

    reports = rpc.search_read(
        "ir.actions.report",
        domain,
        fields=["name", "model", "report_name", "report_type", "binding_model_id"],
        limit=100,
        order="model asc, name asc",
        db=db_name,
    )

    return {
        "reports": [
            {
                "id": r["id"],
                "name": r.get("name", ""),
                "model": r.get("model", ""),
                "report_name": r.get("report_name", ""),
                "type": r.get("report_type", ""),
            }
            for r in reports
        ],
        "count": len(reports),
    }


async def odoo_report_get_template(
    rpc: OdooRPC,
    db_name: str,
    report_name: str,
) -> dict[str, Any]:
    """Get the QWeb template XML of a specific report.

    Args:
        report_name: Technical report name (e.g., "sale.report_saleorder").
    """
    # Find the report
    reports = rpc.search_read(
        "ir.actions.report",
        [["report_name", "=", report_name]],
        fields=["name", "model", "report_name"],
        limit=1,
        db=db_name,
    )

    if not reports:
        return {"found": False, "message": f"Report '{report_name}' not found."}

    # Get the QWeb template
    template_name = report_name.replace(".", "_")
    templates = rpc.search_read(
        "ir.ui.view",
        ["|", ("key", "=", report_name), ("key", "like", template_name)],
        fields=["name", "key", "arch", "type"],
        limit=5,
        db=db_name,
    )

    if not templates:
        return {
            "found": True,
            "report": reports[0],
            "templates": [],
            "message": "Report found but no QWeb templates match. Try browsing views for the report.",
        }

    return {
        "found": True,
        "report": reports[0],
        "templates": [
            {
                "id": t["id"],
                "name": t.get("name", ""),
                "key": t.get("key", ""),
                "arch": t.get("arch", ""),
            }
            for t in templates
        ],
    }


async def odoo_report_modify(
    rpc: OdooRPC,
    db_name: str,
    template_id: int,
    xpath_specs: list[dict],
    view_name: str | None = None,
) -> dict[str, Any]:
    """Modify a QWeb report template using XPath inheritance.

    Args:
        template_id: ID of the QWeb template view to inherit from.
        xpath_specs: List of XPath modifications.
            Each: {"expr": "//div[@class='page']", "position": "inside", "content": "..."}
        view_name: Optional name for the inheriting view.
    """
    if not xpath_specs:
        return {"status": "error", "message": "No xpath_specs provided."}

    parent = rpc.read(
        "ir.ui.view", [template_id],
        fields=["name", "key", "type"],
        db=db_name,
    )
    if not parent:
        return {"status": "error", "message": f"Template {template_id} not found."}

    parent_view = parent[0]
    template_key = parent_view.get("key", f"template_{template_id}")
    arch = build_qweb_inherit_xml(template_key, xpath_specs)

    name = view_name or f"{parent_view['name']} (Custom)"

    existing = rpc.search_read(
        "ir.ui.view",
        [["name", "=", name], ["inherit_id", "=", template_id]],
        fields=["id"],
        limit=1,
        db=db_name,
    )

    if existing:
        rpc.write("ir.ui.view", [existing[0]["id"]], {"arch": arch}, db=db_name)
        view_id = existing[0]["id"]
        action = "updated"
    else:
        view_id = rpc.create("ir.ui.view", {
            "name": name,
            "type": "qweb",
            "inherit_id": template_id,
            "arch": arch,
            "priority": 99,
        }, db=db_name)
        action = "created"

    return {
        "status": action,
        "view_id": view_id,
        "view_name": name,
        "template_id": template_id,
        "xpath_count": len(xpath_specs),
        "message": f"Report templates customization '{name}' {action}.",
    }


async def odoo_report_preview(
    rpc: OdooRPC,
    db_name: str,
    report_name: str,
    record_ids: list[int],
) -> dict[str, Any]:
    """Generate a report for specific records (returns metadata, not the PDF).

    Args:
        report_name: Technical report name.
        record_ids: List of record IDs to generate the report for.
    """
    if not record_ids:
        return {"status": "error", "message": "No record IDs provided."}

    try:
        result = rpc.execute(
            "ir.actions.report",
            "_render_qweb_html",
            [report_name, record_ids],
            db=db_name,
        )
        return {
            "status": "generated",
            "report_name": report_name,
            "record_count": len(record_ids),
            "html_length": len(result[0]) if isinstance(result, (list, tuple)) and result else 0,
            "message": f"Report generated for {len(record_ids)} record(s).",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Report generation failed: {e}",
            "suggestion": "Check that the report name and record IDs are correct.",
        }


async def odoo_report_reset(
    rpc: OdooRPC,
    db_name: str,
    view_id: int,
    confirm: bool = False,
) -> dict[str, Any]:
    """Remove a custom report template modification.

    Args:
        view_id: ID of the inheriting QWeb view to delete.
        confirm: Must be true to proceed.
    """
    if not confirm:
        return {"status": "cancelled", "message": "Set confirm=true to remove this report customization."}

    views = rpc.read("ir.ui.view", [view_id], fields=["name", "inherit_id", "type"], db=db_name)
    if not views:
        return {"status": "error", "message": f"View {view_id} not found."}

    if not views[0].get("inherit_id"):
        return {"status": "error", "message": "This is a base template, not a customization."}

    rpc.unlink("ir.ui.view", [view_id], db=db_name)

    return {
        "status": "deleted",
        "view_id": view_id,
        "message": f"Report customization '{views[0]['name']}' removed.",
    }


async def odoo_report_layout_configure(
    rpc: OdooRPC,
    db_name: str,
    paperformat: str | None = None,
    logo: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    """Configure report layout settings (paper format, company info).

    Args:
        paperformat: Paper format key (e.g., "A4", "US Letter").
        logo: Base64-encoded company logo image.
        company_name: Company name to display on reports.
    """
    updates: dict[str, Any] = {}

    if paperformat:
        formats = rpc.search_read(
            "report.paperformat",
            [["name", "ilike", paperformat]],
            fields=["id", "name"],
            limit=1,
            db=db_name,
        )
        if formats:
            updates["paperformat_id"] = formats[0]["id"]

    if company_name:
        updates["name"] = company_name
    if logo:
        updates["logo"] = logo

    if not updates:
        return {"status": "error", "message": "No layout settings specified."}

    # Update the main company
    companies = rpc.search_read(
        "res.company",
        [],
        fields=["id"],
        limit=1,
        db=db_name,
    )
    if companies:
        rpc.write("res.company", [companies[0]["id"]], updates, db=db_name)

    return {
        "status": "configured",
        "updates": {k: "..." if k == "logo" else v for k, v in updates.items()},
        "message": "Report layout settings updated.",
    }
