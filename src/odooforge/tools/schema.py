"""Schema extension tools — dynamic field/model creation without custom Python modules."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.docker_client import OdooDocker
from odooforge.connections.xmlrpc_client import OdooRPC
from odooforge.utils.validators import validate_model_name
from odooforge.verification.state_cache import LiveStateCache

logger = logging.getLogger(__name__)

# Valid Odoo field types for schema creation
VALID_FIELD_TYPES = {
    "char", "text", "html", "integer", "float", "monetary",
    "boolean", "date", "datetime", "selection", "binary",
    "many2one", "one2many", "many2many",
}


async def odoo_schema_field_create(
    rpc: OdooRPC,
    docker: OdooDocker,
    cache: LiveStateCache,
    db_name: str,
    model: str,
    field_name: str,
    field_type: str,
    field_label: str,
    required: bool = False,
    selection_options: list[list[str]] | None = None,
    relation_model: str | None = None,
    help_text: str | None = None,
    default_value: str | None = None,
    copied: bool = True,
) -> dict[str, Any]:
    """Create a new custom field on an existing model.

    Fields created this way are stored in Odoo's registry with state='manual'.
    No Python code needed — they survive module upgrades.

    Args:
        model: Target model (e.g., "res.partner").
        field_name: Technical name — MUST start with "x_" (e.g., "x_loyalty_tier").
        field_type: One of: char, text, html, integer, float, monetary, boolean,
            date, datetime, selection, binary, many2one, one2many, many2many.
        field_label: Human-readable label (e.g., "Loyalty Tier").
        required: Whether the field is required.
        selection_options: For selection fields: [["key", "Label"], ...].
        relation_model: For relational fields: target model name.
        help_text: Tooltip text for the field.
        default_value: Default value expression.
        copied: Whether the field is copied on record duplication.
    """
    validate_model_name(model)

    # Validate field name
    if not field_name.startswith("x_"):
        return {
            "status": "error",
            "message": (
                f"Custom field names must start with 'x_'. "
                f"Got '{field_name}' — try 'x_{field_name}' instead."
            ),
        }

    if field_type not in VALID_FIELD_TYPES:
        return {
            "status": "error",
            "message": f"Invalid field type '{field_type}'. Valid types: {sorted(VALID_FIELD_TYPES)}",
        }

    # Check if field already exists
    if cache.is_field_valid(model, field_name):
        return {
            "status": "already_exists",
            "message": f"Field '{field_name}' already exists on model '{model}'.",
        }

    # Validate relational fields
    if field_type in ("many2one", "one2many", "many2many") and not relation_model:
        return {
            "status": "error",
            "message": f"Relational field type '{field_type}' requires 'relation_model' parameter.",
        }

    # Build field record
    values: dict[str, Any] = {
        "name": field_name,
        "model_id": None,  # Will be set below
        "field_description": field_label,
        "ttype": field_type,
        "required": required,
        "copied": copied,
        "state": "manual",
    }

    # Get model ID
    model_records = rpc.search_read(
        "ir.model",
        [["model", "=", model]],
        fields=["id"],
        limit=1,
        db=db_name,
    )
    if not model_records:
        return {"status": "error", "message": f"Model '{model}' not found."}

    values["model_id"] = model_records[0]["id"]

    if selection_options and field_type == "selection":
        values["selection_ids"] = [
            (0, 0, {"value": opt[0], "name": opt[1], "sequence": i * 10})
            for i, opt in enumerate(selection_options)
        ]

    if relation_model:
        values["relation"] = relation_model

    if help_text:
        values["help"] = help_text

    field_id = rpc.create("ir.model.fields", values, db=db_name)

    # Restart Odoo for registry reload
    await docker.restart_service("web")
    await docker.wait_for_healthy(timeout=60)

    # Re-auth and verify
    rpc.uid = None
    rpc.authenticate(db_name)
    cache.refresh_model_fields(model)

    verified = cache.is_field_valid(model, field_name)

    return {
        "status": "created" if verified else "created_unverified",
        "field_id": field_id,
        "model": model,
        "field_name": field_name,
        "field_type": field_type,
        "label": field_label,
        "verified": verified,
        "message": (
            f"Field '{field_label}' ({field_name}) created on {model}."
            + ("" if verified else " ⚠️ Field not yet visible in registry — may need another restart.")
        ),
    }


async def odoo_schema_field_update(
    rpc: OdooRPC,
    cache: LiveStateCache,
    db_name: str,
    model: str,
    field_name: str,
    updates: dict,
) -> dict[str, Any]:
    """Update properties of an existing custom field.

    Only custom fields (x_ prefix) can be modified via this tool.

    Args:
        model: Model the field belongs to.
        field_name: Technical field name (must start with x_).
        updates: Dict of properties to update. Supported: field_description,
            required, help, selection_ids, copied.
    """
    validate_model_name(model)

    if not field_name.startswith("x_"):
        return {
            "status": "error",
            "message": "Only custom fields (x_ prefix) can be modified via this tool.",
        }

    # Find the field record
    fields = rpc.search_read(
        "ir.model.fields",
        [["model", "=", model], ["name", "=", field_name], ["state", "=", "manual"]],
        fields=["id"],
        limit=1,
        db=db_name,
    )

    if not fields:
        return {
            "status": "error",
            "message": f"Custom field '{field_name}' not found on model '{model}'.",
        }

    rpc.write("ir.model.fields", [fields[0]["id"]], updates, db=db_name)

    return {
        "status": "updated",
        "model": model,
        "field_name": field_name,
        "updates": updates,
        "message": f"Field '{field_name}' on {model} updated.",
    }


async def odoo_schema_field_delete(
    rpc: OdooRPC,
    docker: OdooDocker,
    cache: LiveStateCache,
    db_name: str,
    model: str,
    field_name: str,
    confirm: bool = False,
) -> dict[str, Any]:
    """Delete a custom field from a model.

    ⚠️ This permanently removes the field and all its data.

    Args:
        model: Model the field belongs to.
        field_name: Technical field name (must start with x_).
        confirm: Must be true to proceed.
    """
    if not confirm:
        return {
            "status": "cancelled",
            "message": (
                f"Set confirm=true to delete field '{field_name}' from {model}. "
                "⚠️ This removes all data in this field permanently."
            ),
        }

    if not field_name.startswith("x_"):
        return {
            "status": "error",
            "message": "Only custom fields (x_ prefix) can be deleted.",
        }

    validate_model_name(model)

    fields = rpc.search_read(
        "ir.model.fields",
        [["model", "=", model], ["name", "=", field_name], ["state", "=", "manual"]],
        fields=["id"],
        limit=1,
        db=db_name,
    )

    if not fields:
        return {"status": "error", "message": f"Custom field '{field_name}' not found on {model}."}

    rpc.unlink("ir.model.fields", [fields[0]["id"]], db=db_name)

    # Restart for registry reload
    await docker.restart_service("web")
    await docker.wait_for_healthy(timeout=60)
    rpc.uid = None
    rpc.authenticate(db_name)
    cache.refresh_model_fields(model)

    return {
        "status": "deleted",
        "model": model,
        "field_name": field_name,
        "message": f"Field '{field_name}' deleted from {model}. Registry reloaded.",
    }


async def odoo_schema_model_create(
    rpc: OdooRPC,
    docker: OdooDocker,
    cache: LiveStateCache,
    db_name: str,
    model_name: str,
    model_label: str,
    fields: list[dict] | None = None,
) -> dict[str, Any]:
    """Create a new custom model (database table).

    The model is created with state='manual' and persists across upgrades.

    Args:
        model_name: Technical name — MUST start with "x_" (e.g., "x_loyalty.program").
        model_label: Human-readable name (e.g., "Loyalty Program").
        fields: Optional list of fields to create along with the model.
            Each: {"name": "x_...", "type": "char", "label": "..."}.
    """
    if not model_name.startswith("x_"):
        return {
            "status": "error",
            "message": f"Custom model names must start with 'x_'. Got '{model_name}'.",
        }

    # Create the model
    values: dict[str, Any] = {
        "name": model_label,
        "model": model_name,
        "state": "manual",
    }

    # Add fields if provided
    if fields:
        field_commands = []
        for f in fields:
            fname = f.get("name", "")
            if not fname.startswith("x_"):
                fname = f"x_{fname}"
            field_commands.append((0, 0, {
                "name": fname,
                "field_description": f.get("label", fname),
                "ttype": f.get("type", "char"),
                "state": "manual",
            }))
        values["field_id"] = field_commands

    model_id = rpc.create("ir.model", values, db=db_name)

    # Restart for registry reload
    await docker.restart_service("web")
    await docker.wait_for_healthy(timeout=60)
    rpc.uid = None
    rpc.authenticate(db_name)
    cache.refresh_models()

    return {
        "status": "created",
        "model_id": model_id,
        "model_name": model_name,
        "label": model_label,
        "fields_created": len(fields) if fields else 0,
        "message": f"Model '{model_label}' ({model_name}) created. Registry reloaded.",
    }


async def odoo_schema_list_custom(
    rpc: OdooRPC,
    db_name: str,
) -> dict[str, Any]:
    """List all custom (manually created) fields and models."""
    # Custom models
    custom_models = rpc.search_read(
        "ir.model",
        [["state", "=", "manual"]],
        fields=["model", "name"],
        limit=100,
        order="model asc",
        db=db_name,
    )

    # Custom fields
    custom_fields = rpc.search_read(
        "ir.model.fields",
        [["state", "=", "manual"]],
        fields=["name", "field_description", "model", "ttype"],
        limit=200,
        order="model asc, name asc",
        db=db_name,
    )

    return {
        "custom_models": [
            {"model": m["model"], "name": m["name"]}
            for m in custom_models
        ],
        "custom_fields": [
            {
                "field": f["name"],
                "label": f.get("field_description", ""),
                "model": f["model"],
                "type": f.get("ttype", ""),
            }
            for f in custom_fields
        ],
        "model_count": len(custom_models),
        "field_count": len(custom_fields),
    }
