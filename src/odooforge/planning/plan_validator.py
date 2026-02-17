"""Plan validator — pre-flight checks before executing a plan."""
from __future__ import annotations
from typing import Any
from odooforge.knowledge import get_knowledge_base


def validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Validate an execution plan. Returns checks and recommendations.

    Static validation only (no live instance needed).
    For live validation, use validate_plan_live().
    """
    kb = get_knowledge_base()
    checks = []
    recommendations = []

    # Check 1: Module compatibility
    all_modules = set()
    for phase in plan.get("phases", []):
        for step in phase.get("steps", []):
            if step.get("tool") == "odoo_module_install":
                mods = step.get("params", {}).get("module_names", [])
                all_modules.update(mods)

    known_modules = set(kb.get_modules().keys())
    unknown = all_modules - known_modules
    if unknown:
        checks.append({
            "check": "module_compatibility",
            "status": "warning",
            "detail": f"Modules not in knowledge base (may still exist in Odoo): {', '.join(sorted(unknown))}",
        })
    else:
        checks.append({
            "check": "module_compatibility",
            "status": "pass",
            "detail": f"All {len(all_modules)} modules are in the knowledge base",
        })

    # Check 2: Field naming conventions
    field_issues = []
    for phase in plan.get("phases", []):
        for step in phase.get("steps", []):
            if step.get("tool") == "odoo_schema_field_create":
                field_name = step.get("params", {}).get("field_name", "")
                if field_name and not field_name.startswith("x_"):
                    field_issues.append(field_name)

    if field_issues:
        checks.append({
            "check": "field_naming",
            "status": "fail",
            "detail": f"Fields missing x_ prefix: {', '.join(field_issues)}",
        })
    else:
        checks.append({
            "check": "field_naming",
            "status": "pass",
            "detail": "All custom fields use x_ prefix",
        })

    # Check 3: Dependency ordering
    phase_nums = {p["phase"] for p in plan.get("phases", [])}
    dep_issues = []
    for phase in plan.get("phases", []):
        for dep in phase.get("depends_on", []):
            if dep not in phase_nums:
                dep_issues.append(f"Phase {phase['phase']} depends on non-existent phase {dep}")
            if dep >= phase["phase"]:
                dep_issues.append(f"Phase {phase['phase']} depends on later phase {dep}")

    if dep_issues:
        checks.append({
            "check": "dependency_order",
            "status": "fail",
            "detail": "; ".join(dep_issues),
        })
    else:
        checks.append({
            "check": "dependency_order",
            "status": "pass",
            "detail": "All phase dependencies are valid and acyclic",
        })

    # Check 4: Has snapshot step
    has_snapshot = any(
        step.get("tool") == "odoo_snapshot_create"
        for phase in plan.get("phases", [])
        for step in phase.get("steps", [])
    )
    if has_snapshot:
        checks.append({
            "check": "safety_snapshot",
            "status": "pass",
            "detail": "Plan includes a snapshot step for rollback safety",
        })
    else:
        checks.append({
            "check": "safety_snapshot",
            "status": "warning",
            "detail": "No snapshot step found — recommend adding one before changes",
        })
        recommendations.append("Add odoo_snapshot_create as the first step for rollback safety")

    # Overall assessment
    has_failures = any(c["status"] == "fail" for c in checks)
    has_warnings = any(c["status"] == "warning" for c in checks)

    return {
        "valid": not has_failures,
        "checks": checks,
        "recommendations": recommendations,
        "summary": {
            "total_checks": len(checks),
            "passed": sum(1 for c in checks if c["status"] == "pass"),
            "warnings": sum(1 for c in checks if c["status"] == "warning"),
            "failures": sum(1 for c in checks if c["status"] == "fail"),
        },
    }
