"""Feature creation workflow — build a complete feature in one call."""

from __future__ import annotations

from typing import Any


def create_feature(
    feature_name: str,
    target_model: str,
    fields: list[dict[str, Any]],
    db_name: str,
    add_to_views: bool = True,
    automation: dict[str, Any] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Generate a step-by-step plan to create a complete feature on a model.

    Each field dict should have at least ``name``, ``type``, and ``label``.
    Optionally provide ``automation`` dict with ``name``, ``trigger``,
    ``model``, and ``action`` keys.
    """
    steps: list[dict[str, Any]] = []
    step_num = 1

    # 1. Safety snapshot
    steps.append({
        "step": step_num,
        "tool": "odoo_snapshot_create",
        "params": {
            "db_name": db_name,
            "name": f"before_feature_{feature_name.lower().replace(' ', '_')}",
            "description": f"Safety snapshot before adding feature '{feature_name}'",
        },
        "description": "Create safety snapshot",
    })
    step_num += 1

    # 2. Create each field
    for field in fields:
        field_name = field["name"]
        field_type = field["type"]
        field_label = field.get(
            "label",
            field_name.replace("x_", "").replace("_", " ").title(),
        )
        steps.append({
            "step": step_num,
            "tool": "odoo_schema_field_create",
            "params": {
                "db_name": db_name,
                "model": target_model,
                "field_name": field_name,
                "field_type": field_type,
                "field_label": field_label,
            },
            "description": f"Create field {field_name} ({field_type}) on {target_model}",
        })
        step_num += 1

    # 3. Add fields to views
    if add_to_views and fields:
        # Build XML snippets for form view insertion
        field_xml_nodes = " ".join(
            f'<field name="{f["name"]}"/>' for f in fields
        )

        steps.append({
            "step": step_num,
            "tool": "odoo_view_modify",
            "params": {
                "db_name": db_name,
                "model": target_model,
                "view_type": "form",
                "arch_snippet": f'<group string="{feature_name}">{field_xml_nodes}</group>',
            },
            "description": f"Add {feature_name} fields to form view",
        })
        step_num += 1

        # Tree view: add each field as a column
        tree_field_nodes = " ".join(
            f'<field name="{f["name"]}"/>' for f in fields
        )
        steps.append({
            "step": step_num,
            "tool": "odoo_view_modify",
            "params": {
                "db_name": db_name,
                "model": target_model,
                "view_type": "tree",
                "arch_snippet": tree_field_nodes,
            },
            "description": f"Add {feature_name} fields to tree view",
        })
        step_num += 1

    # 4. Optional automation
    if automation:
        steps.append({
            "step": step_num,
            "tool": "odoo_automation_create",
            "params": {
                "db_name": db_name,
                "name": automation.get("name", f"{feature_name} automation"),
                "model": automation.get("model", target_model),
                "trigger": automation.get("trigger", "on_create"),
            },
            "description": f"Create automation: {automation.get('name', feature_name + ' automation')}",
        })
        step_num += 1

    # 5. Verify by reading the model fields back
    steps.append({
        "step": step_num,
        "tool": "odoo_model_fields",
        "params": {"db_name": db_name, "model": target_model},
        "description": f"Verify fields on {target_model}",
    })

    return {
        "workflow": "create_feature",
        "feature_name": feature_name,
        "target_model": target_model,
        "db_name": db_name,
        "steps": steps,
        "summary": {
            "total_steps": len(steps),
            "fields_to_create": len(fields),
            "views_modified": 2 if (add_to_views and fields) else 0,
            "automation": automation is not None,
        },
        "dry_run": dry_run,
    }
