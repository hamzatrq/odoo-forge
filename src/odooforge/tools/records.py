"""Record CRUD tools — search, read, create, update, delete, execute."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC
from odooforge.utils.formatting import format_records
from odooforge.utils.validators import validate_domain, validate_model_name
from odooforge.verification.state_cache import LiveStateCache

logger = logging.getLogger(__name__)


async def odoo_record_search(
    rpc: OdooRPC,
    db_name: str,
    model: str,
    domain: list | None = None,
    fields: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
    order: str | None = None,
) -> dict[str, Any]:
    """Search for records in any Odoo model.

    Args:
        model: Technical model name (e.g., "res.partner", "sale.order").
        domain: Odoo domain filter (e.g., [["is_company", "=", true]]).
            Empty list [] returns all records.
        fields: List of field names to return. If empty, returns key fields.
        limit: Max records to return (default 20, max 200).
        offset: Skip this many records (for pagination).
        order: Sort order (e.g., "name asc", "create_date desc").
    """
    validate_model_name(model)
    search_domain = validate_domain(domain or [])
    limit = min(limit, 200)

    records = rpc.search_read(
        model, search_domain,
        fields=fields,
        limit=limit,
        offset=offset,
        order=order,
        db=db_name,
    )

    total = rpc.search_count(model, search_domain, db=db_name)

    return {
        "model": model,
        "records": records,
        "count": len(records),
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + len(records)) < total,
    }


async def odoo_record_read(
    rpc: OdooRPC,
    db_name: str,
    model: str,
    ids: list[int],
    fields: list[str] | None = None,
) -> dict[str, Any]:
    """Read specific records by ID.

    Args:
        model: Technical model name.
        ids: List of record IDs to read.
        fields: Fields to return. If empty, returns all fields.
    """
    validate_model_name(model)

    if not ids:
        return {"model": model, "records": [], "count": 0}

    records = rpc.read(model, ids, fields=fields, db=db_name)

    return {
        "model": model,
        "records": records,
        "count": len(records),
    }


async def odoo_record_create(
    rpc: OdooRPC,
    cache: LiveStateCache,
    db_name: str,
    model: str,
    values: dict | list[dict],
) -> dict[str, Any]:
    """Create one or more records in any Odoo model.

    Args:
        model: Technical model name (e.g., "res.partner").
        values: Field values dict, or list of dicts for bulk creation.
            Example: {"name": "Steamin", "email": "info@steamin.pk"}
    """
    validate_model_name(model)

    # Validate field names against live schema
    sample = values if isinstance(values, dict) else values[0]
    invalid_fields = cache.validate_fields(model, list(sample.keys()))
    if invalid_fields:
        # Fetch current valid fields for helpful error
        model_fields = cache.get_model_fields(model) or {}
        available = sorted(model_fields.keys())[:50]
        return {
            "status": "error",
            "invalid_fields": invalid_fields,
            "message": (
                f"Fields {invalid_fields} do not exist on model '{model}'. "
                f"Available fields (sample): {available}"
            ),
        }

    result_ids = rpc.create(model, values, db=db_name)

    # Normalize to list
    if isinstance(result_ids, int):
        result_ids = [result_ids]

    record_count = len(values) if isinstance(values, list) else 1

    return {
        "status": "created",
        "model": model,
        "ids": result_ids,
        "count": record_count,
        "message": f"Created {record_count} record(s) in {model}.",
    }


async def odoo_record_update(
    rpc: OdooRPC,
    cache: LiveStateCache,
    db_name: str,
    model: str,
    ids: list[int],
    values: dict,
) -> dict[str, Any]:
    """Update existing records.

    Args:
        model: Technical model name.
        ids: Record IDs to update.
        values: Field values to set.
    """
    validate_model_name(model)

    if not ids:
        return {"status": "error", "message": "No record IDs provided."}

    # Validate field names
    invalid_fields = cache.validate_fields(model, list(values.keys()))
    if invalid_fields:
        return {
            "status": "error",
            "invalid_fields": invalid_fields,
            "message": f"Fields {invalid_fields} do not exist on model '{model}'.",
        }

    rpc.write(model, ids, values, db=db_name)

    return {
        "status": "updated",
        "model": model,
        "ids": ids,
        "updated_count": len(ids),
        "message": f"Updated {len(ids)} record(s) in {model}.",
    }


async def odoo_record_delete(
    rpc: OdooRPC,
    db_name: str,
    model: str,
    ids: list[int],
    confirm: bool = False,
) -> dict[str, Any]:
    """Delete records from any model.

    Args:
        model: Technical model name.
        ids: Record IDs to delete.
        confirm: Must be true to confirm deletion.
    """
    if not confirm:
        return {
            "status": "cancelled",
            "message": f"Set confirm=true to delete {len(ids)} record(s) from {model}. This cannot be undone.",
        }

    validate_model_name(model)

    if not ids:
        return {"status": "error", "message": "No record IDs provided."}

    rpc.unlink(model, ids, db=db_name)

    return {
        "status": "deleted",
        "model": model,
        "ids": ids,
        "deleted_count": len(ids),
        "message": f"Deleted {len(ids)} record(s) from {model}.",
    }


async def odoo_record_execute(
    rpc: OdooRPC,
    db_name: str,
    model: str,
    method: str,
    args: list | None = None,
    kwargs: dict | None = None,
) -> dict[str, Any]:
    """Execute any method on any model (generic escape hatch).

    Args:
        model: Technical model name.
        method: Method name to call.
        args: Positional arguments.
        kwargs: Keyword arguments.
    """
    validate_model_name(model)

    result = rpc.execute_method(
        model, method,
        args=args or [],
        kwargs=kwargs or {},
        db=db_name,
    )

    return {
        "model": model,
        "method": method,
        "result": result,
    }
