"""View management tools — list, get arch, modify, reset, list customizations."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.docker_client import OdooDocker
from odooforge.connections.xmlrpc_client import OdooRPC
from odooforge.utils.validators import validate_model_name
from odooforge.utils.xpath_builder import build_inherit_xml
from odooforge.verification.state_cache import LiveStateCache

logger = logging.getLogger(__name__)


async def odoo_view_list(
    rpc: OdooRPC,
    db_name: str,
    model: str | None = None,
    view_type: str | None = None,
) -> dict[str, Any]:
    """List views, optionally filtered by model or type.

    Args:
        model: Filter views for this model (e.g., "res.partner").
        view_type: Filter by type: form, tree, kanban, search, qweb, etc.
    """
    domain: list = []
    if model:
        validate_model_name(model)
        domain.append(("model", "=", model))
    if view_type:
        domain.append(("type", "=", view_type))

    views = rpc.search_read(
        "ir.ui.view",
        domain,
        fields=["name", "model", "type", "inherit_id", "priority", "active"],
        limit=100,
        order="model asc, priority asc",
        db=db_name,
    )

    return {
        "views": [
            {
                "id": v["id"],
                "name": v.get("name", ""),
                "model": v.get("model", ""),
                "type": v.get("type", ""),
                "inherits": v["inherit_id"][1] if isinstance(v.get("inherit_id"), (list, tuple)) else None,
                "priority": v.get("priority", 16),
                "active": v.get("active", True),
            }
            for v in views
        ],
        "count": len(views),
    }


async def odoo_view_get_arch(
    rpc: OdooRPC,
    db_name: str,
    view_id: int | None = None,
    model: str | None = None,
    view_type: str = "form",
) -> dict[str, Any]:
    """Get the full architecture XML of a view.

    Either specify view_id directly, or model+view_type to get the default view.

    Args:
        view_id: Specific view ID.
        model: Model name (used with view_type to find default view).
        view_type: View type (form, tree, kanban, search).
    """
    if view_id:
        views = rpc.read("ir.ui.view", [view_id], fields=["name", "model", "type", "arch"], db=db_name)
        if not views:
            return {"found": False, "message": f"View ID {view_id} not found."}
        v = views[0]
    elif model:
        validate_model_name(model)
        try:
            result = rpc.execute(
                model, "get_view", [], {"view_type": view_type}, db=db_name,
            )
            return {
                "found": True,
                "view_id": result.get("view_id"),
                "model": model,
                "type": view_type,
                "arch": result.get("arch", ""),
            }
        except Exception as e:
            return {"found": False, "message": f"Could not get view: {e}"}
    else:
        return {"found": False, "message": "Provide either view_id or model name."}

    return {
        "found": True,
        "view_id": v["id"],
        "name": v.get("name", ""),
        "model": v.get("model", ""),
        "type": v.get("type", ""),
        "arch": v.get("arch", ""),
    }


async def odoo_view_modify(
    rpc: OdooRPC,
    docker: OdooDocker,
    db_name: str,
    inherit_view_id: int,
    view_name: str,
    xpath_specs: list[dict],
) -> dict[str, Any]:
    """Create or update an inheriting view to modify an existing view.

    Uses XPath expressions to target specific elements and inject content.

    Args:
        inherit_view_id: ID of the parent view to inherit from.
        view_name: Name for the new inheriting view.
        xpath_specs: List of XPath modifications.
            Each: {"expr": "//field[@name='email']", "position": "after",
                   "content": "<field name='x_custom'/>"}
    """
    if not xpath_specs:
        return {"status": "error", "message": "No xpath_specs provided."}

    # Get parent view info
    parent = rpc.read(
        "ir.ui.view", [inherit_view_id],
        fields=["model", "type", "name"],
        db=db_name,
    )
    if not parent:
        return {"status": "error", "message": f"Parent view {inherit_view_id} not found."}

    parent_view = parent[0]
    arch = build_inherit_xml(xpath_specs)

    # Check if we already have a view with this name
    existing = rpc.search_read(
        "ir.ui.view",
        [["name", "=", view_name], ["inherit_id", "=", inherit_view_id]],
        fields=["id"],
        limit=1,
        db=db_name,
    )

    if existing:
        # Update existing
        rpc.write("ir.ui.view", [existing[0]["id"]], {"arch": arch}, db=db_name)
        view_id = existing[0]["id"]
        action = "updated"
    else:
        # Create new
        view_id = rpc.create("ir.ui.view", {
            "name": view_name,
            "model": parent_view["model"],
            "type": parent_view["type"],
            "inherit_id": inherit_view_id,
            "arch": arch,
            "priority": 99,
        }, db=db_name)
        action = "created"

    return {
        "status": action,
        "view_id": view_id,
        "view_name": view_name,
        "parent_view": parent_view["name"],
        "model": parent_view["model"],
        "xpath_count": len(xpath_specs),
        "arch": arch,
        "message": f"Inheriting view '{view_name}' {action} (ID: {view_id}).",
    }


async def odoo_view_reset(
    rpc: OdooRPC,
    db_name: str,
    view_id: int,
    confirm: bool = False,
) -> dict[str, Any]:
    """Delete a custom inheriting view, reverting the parent to its original state.

    Args:
        view_id: ID of the inheriting view to delete.
        confirm: Must be true to proceed.
    """
    if not confirm:
        return {
            "status": "cancelled",
            "message": "Set confirm=true to delete this view customization.",
        }

    views = rpc.read(
        "ir.ui.view", [view_id],
        fields=["name", "inherit_id"],
        db=db_name,
    )
    if not views:
        return {"status": "error", "message": f"View {view_id} not found."}

    if not views[0].get("inherit_id"):
        return {
            "status": "error",
            "message": "This is a base view, not a customization. Cannot reset.",
        }

    rpc.unlink("ir.ui.view", [view_id], db=db_name)

    return {
        "status": "deleted",
        "view_id": view_id,
        "view_name": views[0]["name"],
        "message": f"View customization '{views[0]['name']}' removed.",
    }


async def odoo_view_list_customizations(
    rpc: OdooRPC,
    db_name: str,
    model: str | None = None,
) -> dict[str, Any]:
    """List all custom (inheriting) views, optionally for a specific model.

    These are the views created by odoo_view_modify that can be reset.
    """
    domain: list = [("inherit_id", "!=", False)]
    if model:
        validate_model_name(model)
        domain.append(("model", "=", model))

    # Focus on high-priority (custom) views
    views = rpc.search_read(
        "ir.ui.view",
        domain,
        fields=["name", "model", "type", "inherit_id", "priority", "active"],
        limit=100,
        order="model asc, priority desc",
        db=db_name,
    )

    return {
        "customizations": [
            {
                "id": v["id"],
                "name": v.get("name", ""),
                "model": v.get("model", ""),
                "type": v.get("type", ""),
                "parent": v["inherit_id"][1] if isinstance(v.get("inherit_id"), (list, tuple)) else None,
                "priority": v.get("priority", 16),
                "active": v.get("active", True),
            }
            for v in views
        ],
        "count": len(views),
    }
