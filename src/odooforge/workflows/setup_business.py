"""Business setup workflow — full company setup from an industry blueprint."""

from __future__ import annotations

from typing import Any


def setup_business(
    blueprint_name: str,
    company_name: str,
    db_name: str,
    locations: int = 1,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Generate a step-by-step execution plan for full business setup.

    Looks up the given blueprint in the knowledge base and produces an
    ordered list of tool-call steps that an MCP client can execute
    sequentially.
    """
    from odooforge.knowledge import get_knowledge_base

    kb = get_knowledge_base()
    bp = kb.get_blueprint(blueprint_name)

    if not bp:
        available = kb.list_blueprints()
        return {
            "status": "error",
            "message": f"Unknown blueprint '{blueprint_name}'",
            "available": available,
        }

    steps: list[dict[str, Any]] = []
    step_num = 1

    # 1. Safety snapshot
    steps.append({
        "step": step_num,
        "tool": "odoo_snapshot_create",
        "params": {
            "db_name": db_name,
            "name": f"before_{blueprint_name}_setup",
            "description": f"Safety snapshot before {blueprint_name} business setup",
        },
        "description": "Create safety snapshot",
    })
    step_num += 1

    # 2. Company configuration
    steps.append({
        "step": step_num,
        "tool": "odoo_company_configure",
        "params": {"db_name": db_name, "name": company_name},
        "description": f"Configure company as '{company_name}'",
    })
    step_num += 1

    # 3. Install required modules
    steps.append({
        "step": step_num,
        "tool": "odoo_module_install",
        "params": {"db_name": db_name, "module_names": bp.get("modules", [])},
        "description": f"Install {len(bp.get('modules', []))} modules",
    })
    step_num += 1

    # 4. Apply blueprint settings
    if bp.get("settings"):
        steps.append({
            "step": step_num,
            "tool": "odoo_settings_set",
            "params": {"db_name": db_name, **bp["settings"]},
            "description": "Apply blueprint settings",
        })
        step_num += 1

    # 5. Create custom fields from blueprint models
    for model_spec in bp.get("models", []):
        if model_spec.get("action") == "extend":
            for field in model_spec.get("fields", []):
                label = field.get(
                    "label",
                    field.get(
                        "string",
                        field["name"].replace("x_", "").replace("_", " ").title(),
                    ),
                )
                steps.append({
                    "step": step_num,
                    "tool": "odoo_schema_field_create",
                    "params": {
                        "db_name": db_name,
                        "model": model_spec["model"],
                        "field_name": field["name"],
                        "field_type": field["type"],
                        "field_label": label,
                    },
                    "description": f"Add {field['name']} to {model_spec['model']}",
                })
                step_num += 1

    # 6. Multi-location support
    if locations > 1:
        steps.append({
            "step": step_num,
            "tool": "odoo_settings_set",
            "params": {"db_name": db_name, "group_multi_company": True},
            "description": "Enable multi-company mode",
        })
        step_num += 1
        for i in range(2, locations + 1):
            steps.append({
                "step": step_num,
                "tool": "odoo_record_create",
                "params": {
                    "db_name": db_name,
                    "model": "res.company",
                    "values": {"name": f"{company_name} - Location {i}"},
                },
                "description": f"Create branch company for location {i}",
            })
            step_num += 1

    # 7. Automations from blueprint
    for auto in bp.get("automations", []):
        steps.append({
            "step": step_num,
            "tool": "odoo_automation_create",
            "params": {
                "db_name": db_name,
                "name": auto.get("name", "Automation"),
                "model": auto.get("model", ""),
                "trigger": auto.get("trigger", "on_create"),
            },
            "description": f"Create automation: {auto.get('name', 'unnamed')}",
        })
        step_num += 1

    # 8. Health check
    steps.append({
        "step": step_num,
        "tool": "odoo_diagnostics_health_check",
        "params": {"db_name": db_name},
        "description": "Run health check to verify setup",
    })

    # Count custom fields across extended models
    custom_field_count = sum(
        len(m.get("fields", []))
        for m in bp.get("models", [])
        if m.get("action") == "extend"
    )

    return {
        "workflow": "setup_business",
        "blueprint": blueprint_name,
        "company_name": company_name,
        "db_name": db_name,
        "steps": steps,
        "summary": {
            "total_steps": len(steps),
            "modules_to_install": len(bp.get("modules", [])),
            "custom_fields": custom_field_count,
            "automations": len(bp.get("automations", [])),
            "locations": locations,
        },
        "dry_run": dry_run,
    }
