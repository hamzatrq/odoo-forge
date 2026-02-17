"""Solution designer — create phased execution plans from requirements."""
from __future__ import annotations
from typing import Any
from odooforge.knowledge import get_knowledge_base


def design_solution(
    requirements: dict[str, Any],
    user_answers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Turn analyzed requirements into a phased execution plan.

    Returns a DAG of phases with tool calls for each step.
    """
    kb = get_knowledge_base()
    user_answers = user_answers or {}

    phases = []
    phase_num = 1

    # Phase 1: Foundation (always present)
    foundation_steps = _build_foundation_phase(requirements, kb)
    phases.append({
        "phase": phase_num,
        "name": "Foundation",
        "depends_on": [],
        "steps": foundation_steps,
    })
    phase_num += 1

    # Phase 2: Multi-location (if needed)
    infra = requirements.get("infrastructure", {})
    if infra.get("multi_company") and infra.get("locations", 0) > 1:
        multi_steps = _build_multi_location_phase(requirements, user_answers)
        phases.append({
            "phase": phase_num,
            "name": "Multi-Location Setup",
            "depends_on": [1],
            "steps": multi_steps,
        })
        phase_num += 1

    # Phase N: Custom features (one phase per custom requirement)
    for req in requirements.get("custom_requirements", []):
        feature_steps = _build_feature_phase(req)
        phases.append({
            "phase": phase_num,
            "name": req.get("description", "Custom Feature")[:50],
            "depends_on": [1],
            "steps": feature_steps,
        })
        phase_num += 1

    # Phase N+1: Integrations (if needed)
    if infra.get("needs_website") or infra.get("needs_delivery"):
        integration_steps = _build_integration_phase(infra, user_answers)
        if integration_steps:
            phases.append({
                "phase": phase_num,
                "name": "Integrations",
                "depends_on": [1],
                "steps": integration_steps,
            })
            phase_num += 1

    # Final phase: Verification (depends on all previous)
    all_phase_nums = [p["phase"] for p in phases]
    phases.append({
        "phase": phase_num,
        "name": "Verification",
        "depends_on": all_phase_nums,
        "steps": [
            {
                "tool": "odoo_diagnostics_health_check",
                "params": {},
                "description": "Run full system health check",
            }
        ],
    })

    # Identify parallelizable phases (those that only depend on phase 1)
    parallelizable = [
        p["phase"] for p in phases
        if p["depends_on"] == [1] and p["phase"] != 1
    ]

    return {
        "plan_id": f"{requirements.get('industry', 'custom')}-setup",
        "phases": phases,
        "summary": {
            "total_phases": len(phases),
            "total_steps": sum(len(p["steps"]) for p in phases),
            "parallelizable": parallelizable if len(parallelizable) > 1 else [],
            "requires_code_generation": any(
                r.get("approach") == "code_generation"
                for r in requirements.get("custom_requirements", [])
            ),
        },
    }


def _build_foundation_phase(requirements: dict, kb) -> list[dict]:
    """Build the foundation phase: snapshot + modules + settings."""
    steps = []

    # Step 1: Create snapshot
    steps.append({
        "tool": "odoo_snapshot_create",
        "params": {},
        "description": "Create safety snapshot before setup",
    })

    # Step 2: Install modules
    modules = [m["module"] for m in requirements.get("modules_needed", [])]
    if modules:
        steps.append({
            "tool": "odoo_module_install",
            "params": {"module_names": modules},
            "description": f"Install {len(modules)} modules: {', '.join(modules[:5])}{'...' if len(modules) > 5 else ''}",
        })

    # Step 3: Apply blueprint settings if available
    blueprint_id = requirements.get("matching_blueprint")
    if blueprint_id:
        bp = kb.get_blueprint(blueprint_id)
        if bp and bp.get("settings"):
            steps.append({
                "tool": "odoo_settings_set",
                "params": {"settings": bp["settings"]},
                "description": f"Apply {blueprint_id} configuration settings",
            })

    # Step 4: Create custom fields from blueprint models
    if blueprint_id:
        bp = kb.get_blueprint(blueprint_id)
        if bp:
            for model_spec in bp.get("models", []):
                if model_spec.get("action") == "extend":
                    for field in model_spec.get("fields", []):
                        steps.append({
                            "tool": "odoo_schema_field_create",
                            "params": {
                                "model": model_spec["model"],
                                "field_name": field["name"],
                                "field_type": field["type"],
                            },
                            "description": f"Add {field['name']} to {model_spec['model']}",
                        })

    return steps


def _build_multi_location_phase(requirements: dict, user_answers: dict) -> list[dict]:
    """Build multi-location/multi-company setup phase."""
    steps = []
    infra = requirements.get("infrastructure", {})
    locations = infra.get("locations", 2)

    steps.append({
        "tool": "odoo_settings_set",
        "params": {"multi_company": True},
        "description": "Enable multi-company mode",
    })

    for i in range(1, locations + 1):
        steps.append({
            "tool": "odoo_record_create",
            "params": {
                "model": "res.company",
                "values": {"name": f"Location {i}"},
            },
            "description": f"Create branch company for location {i}",
        })

    return steps


def _build_feature_phase(requirement: dict) -> list[dict]:
    """Build a custom feature phase from a requirement."""
    steps = []
    pattern = requirement.get("pattern", "")
    approach = requirement.get("approach", "configuration")

    if approach == "configuration":
        if "partner" in pattern:
            steps.append({
                "tool": "odoo_schema_field_create",
                "params": {"model": "res.partner"},
                "description": f"Create custom fields on contacts for: {requirement.get('description', pattern)[:40]}",
            })
        elif "product" in pattern:
            steps.append({
                "tool": "odoo_schema_field_create",
                "params": {"model": "product.template"},
                "description": f"Create custom fields on products for: {requirement.get('description', pattern)[:40]}",
            })

        if "automated" in pattern or "workflow" in pattern:
            steps.append({
                "tool": "odoo_automation_create",
                "params": {},
                "description": f"Create automation for: {requirement.get('description', pattern)[:40]}",
            })

        if "report" in pattern:
            steps.append({
                "tool": "odoo_report_modify",
                "params": {},
                "description": f"Create/modify report: {requirement.get('description', pattern)[:40]}",
            })
        if "import" in pattern or "data" in pattern:
            steps.append({
                "tool": "odoo_import_execute",
                "params": {},
                "description": f"Set up data import for: {requirement.get('description', pattern)[:40]}",
            })
    else:
        steps.append({
            "tool": "odoo_generate_addon",
            "params": {},
            "description": f"Generate custom module for: {requirement.get('description', pattern)[:40]}",
        })

    # Fallback if no steps were generated
    if not steps:
        steps.append({
            "tool": "odoo_schema_field_create",
            "params": {},
            "description": f"Implement: {requirement.get('description', 'custom feature')[:50]}",
        })

    return steps


def _build_integration_phase(infra: dict, user_answers: dict) -> list[dict]:
    """Build integration phase for website, payment, delivery."""
    steps = []

    if infra.get("needs_website"):
        steps.append({
            "tool": "odoo_module_install",
            "params": {"module_names": ["website_sale"]},
            "description": "Install eCommerce module for online selling",
        })

        provider = user_answers.get("payment_provider", "")
        if provider:
            steps.append({
                "tool": "odoo_settings_set",
                "params": {"payment_provider": provider},
                "description": f"Configure {provider} payment provider",
            })

    if infra.get("needs_delivery"):
        steps.append({
            "tool": "odoo_module_install",
            "params": {"module_names": ["delivery"]},
            "description": "Install shipping/delivery module",
        })

    return steps
