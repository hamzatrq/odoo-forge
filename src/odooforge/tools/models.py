"""Model introspection tools — list models, get fields, search fields."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC
from odooforge.utils.validators import validate_model_name
from odooforge.verification.state_cache import LiveStateCache

logger = logging.getLogger(__name__)


async def odoo_model_list(
    rpc: OdooRPC,
    db_name: str,
    search: str | None = None,
    transient: bool = False,
) -> dict[str, Any]:
    """List all available models (database tables) in Odoo.

    Args:
        search: Filter models by name or description (case-insensitive).
        transient: If true, include transient (wizard) models.
    """
    domain: list = []
    if search:
        domain = ["|", ("model", "ilike", search), ("name", "ilike", search)]
    if not transient:
        domain.append(("transient", "=", False))

    models = rpc.search_read(
        "ir.model",
        domain,
        fields=["model", "name", "state", "transient", "count"],
        limit=200,
        order="model asc",
        db=db_name,
    )

    return {
        "models": [
            {
                "model": m["model"],
                "name": m.get("name", ""),
                "type": "custom" if m.get("state") == "manual" else "base",
                "transient": m.get("transient", False),
            }
            for m in models
        ],
        "count": len(models),
    }


async def odoo_model_fields(
    rpc: OdooRPC,
    cache: LiveStateCache,
    db_name: str,
    model: str,
    field_type: str | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    """Get all fields of a model with their types and attributes.

    This is the single source of truth for what fields exist on a model.
    Also used internally to validate field names before write operations.

    Args:
        model: Technical model name (e.g., "res.partner").
        field_type: Filter by field type (e.g., "char", "many2one", "boolean").
        search: Filter fields by name or label (case-insensitive).
    """
    validate_model_name(model)

    # Use fields_get for full metadata
    fields = rpc.fields_get(
        model,
        attributes=["string", "type", "required", "readonly", "relation", "help", "store"],
        db=db_name,
    )

    # Update cache
    cache._model_fields[model] = fields

    result_fields = []
    for fname, fdata in sorted(fields.items()):
        # Apply filters
        if field_type and fdata.get("type") != field_type:
            continue
        if search:
            s = search.lower()
            if s not in fname.lower() and s not in (fdata.get("string") or "").lower():
                continue

        entry = {
            "name": fname,
            "label": fdata.get("string", ""),
            "type": fdata.get("type", ""),
            "required": fdata.get("required", False),
            "readonly": fdata.get("readonly", False),
            "stored": fdata.get("store", True),
        }
        if fdata.get("relation"):
            entry["relation"] = fdata["relation"]
        if fdata.get("help"):
            entry["help"] = fdata["help"][:150]

        result_fields.append(entry)

    return {
        "model": model,
        "fields": result_fields,
        "count": len(result_fields),
        "total_fields": len(fields),
    }


async def odoo_model_search_field(
    rpc: OdooRPC,
    db_name: str,
    query: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Search for fields across all models or within a specific model.

    Useful when you know a field should exist but aren't sure which model it's on.

    Args:
        query: Search term to match against field name or label.
        model: Optional model to search within. If omitted, searches across all models.
    """
    domain: list = [
        "|",
        ("name", "ilike", query),
        ("field_description", "ilike", query),
    ]
    if model:
        validate_model_name(model)
        domain.append(("model", "=", model))

    fields = rpc.search_read(
        "ir.model.fields",
        domain,
        fields=["name", "field_description", "model", "ttype", "relation", "required", "store"],
        limit=50,
        order="model asc, name asc",
        db=db_name,
    )

    return {
        "results": [
            {
                "field": f["name"],
                "label": f.get("field_description", ""),
                "model": f["model"],
                "type": f.get("ttype", ""),
                "relation": f.get("relation", ""),
                "required": f.get("required", False),
                "stored": f.get("store", True),
            }
            for f in fields
        ],
        "count": len(fields),
        "query": query,
    }
