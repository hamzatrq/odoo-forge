"""Batch import tools — preview, execute, template generation."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC
from odooforge.utils.validators import validate_model_name

logger = logging.getLogger(__name__)


async def odoo_import_preview(
    rpc: OdooRPC,
    db_name: str,
    model: str,
    csv_data: str,
    has_header: bool = True,
) -> dict[str, Any]:
    """Preview a CSV import — validate fields and show what would be imported.

    Args:
        model: Target model (e.g., "res.partner").
        csv_data: Raw CSV content.
        has_header: Whether the first row contains field names.
    """
    validate_model_name(model)

    import csv
    import io

    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)

    if not rows:
        return {"status": "error", "message": "Empty CSV data."}

    if has_header:
        headers = rows[0]
        data_rows = rows[1:]
    else:
        # Generate placeholder headers
        headers = [f"column_{i}" for i in range(len(rows[0]))]
        data_rows = rows

    # Validate fields against model
    fields_info = rpc.fields_get(model, db=db_name)
    valid_fields = set(fields_info.keys())
    external_ids_allowed = {"id", ".id", "id/.id"}

    field_mapping = []
    warnings = []
    for h in headers:
        clean = h.strip()
        if clean in valid_fields or clean in external_ids_allowed:
            field_mapping.append({"csv_column": h, "odoo_field": clean, "valid": True})
        elif "/" in clean:
            # Relational field notation: partner_id/name
            base_field = clean.split("/")[0]
            if base_field in valid_fields:
                field_mapping.append({"csv_column": h, "odoo_field": clean, "valid": True})
            else:
                field_mapping.append({"csv_column": h, "odoo_field": clean, "valid": False})
                warnings.append(f"Unknown field: {clean}")
        else:
            field_mapping.append({"csv_column": h, "odoo_field": clean, "valid": False})
            warnings.append(f"Unknown field: {clean}")

    return {
        "status": "preview",
        "model": model,
        "total_rows": len(data_rows),
        "field_mapping": field_mapping,
        "valid_fields": sum(1 for f in field_mapping if f["valid"]),
        "invalid_fields": sum(1 for f in field_mapping if not f["valid"]),
        "warnings": warnings,
        "sample_rows": data_rows[:3],
        "message": f"Preview: {len(data_rows)} rows, {len(headers)} columns. "
                   f"Use odoo_import_execute to proceed.",
    }


async def odoo_import_execute(
    rpc: OdooRPC,
    db_name: str,
    model: str,
    csv_data: str,
    has_header: bool = True,
    on_error: str = "stop",
) -> dict[str, Any]:
    """Execute a CSV import into an Odoo model.

    Args:
        model: Target model.
        csv_data: Raw CSV content.
        has_header: Whether the first row contains field names.
        on_error: Error handling: "stop" (abort on first error) or "skip" (skip bad rows).
    """
    validate_model_name(model)

    import csv
    import io

    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)

    if not rows:
        return {"status": "error", "message": "Empty CSV data."}

    if has_header:
        headers = rows[0]
        data_rows = rows[1:]
    else:
        fields_info = rpc.fields_get(model, db=db_name)
        headers = list(fields_info.keys())[:len(rows[0])]
        data_rows = rows

    # Use Odoo's base_import.import load method
    try:
        result = rpc.load(
            model,
            headers,
            data_rows,
            db=db_name,
        )

        ids = result.get("ids") or []
        messages = result.get("messages") or []
        errors = [m for m in messages if m.get("type") == "error"]
        warnings = [m for m in messages if m.get("type") == "warning"]

        if errors and on_error == "stop":
            return {
                "status": "error",
                "imported": 0,
                "errors": errors[:10],
                "message": f"Import failed with {len(errors)} error(s). First: {errors[0].get('message', '')}",
            }

        return {
            "status": "imported",
            "imported": len(ids),
            "total_rows": len(data_rows),
            "ids": ids[:20],
            "errors": errors[:10] if errors else [],
            "warnings": warnings[:10] if warnings else [],
            "message": f"Successfully imported {len(ids)} record(s) into {model}.",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Import failed: {e}",
            "suggestion": "Check CSV format and field names. Use odoo_import_preview first.",
        }


async def odoo_import_template(
    rpc: OdooRPC,
    db_name: str,
    model: str,
    include_optional: bool = False,
) -> dict[str, Any]:
    """Generate a CSV template for importing records into a model.

    Args:
        model: Target model.
        include_optional: Include optional (non-required) fields.
    """
    validate_model_name(model)

    fields_info = rpc.fields_get(model, db=db_name)

    template_fields = []
    for name, info in fields_info.items():
        if name in ("id", "__last_update", "create_uid", "create_date",
                     "write_uid", "write_date"):
            continue

        is_required = info.get("required", False)
        is_readonly = info.get("readonly", False)

        if is_readonly and not is_required:
            continue

        if is_required or include_optional:
            template_fields.append({
                "field": name,
                "label": info.get("string", name),
                "type": info.get("type", "char"),
                "required": is_required,
                "help": info.get("help", ""),
            })

    # Sort: required first, then alphabetical
    template_fields.sort(key=lambda f: (not f["required"], f["field"]))

    csv_header = ",".join(f["field"] for f in template_fields)

    return {
        "model": model,
        "fields": template_fields,
        "field_count": len(template_fields),
        "csv_header": csv_header,
        "message": f"Template for {model}: {len(template_fields)} fields. "
                   f"Copy the csv_header as your first CSV row.",
    }
