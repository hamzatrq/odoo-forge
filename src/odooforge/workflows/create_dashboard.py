"""Dashboard creation workflow — build a management dashboard."""

from __future__ import annotations

from typing import Any


def create_dashboard(
    dashboard_name: str,
    metrics: list[dict[str, Any]],
    db_name: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Generate a step-by-step plan to create a dashboard with metrics.

    Each metric dict should have ``model``, ``measure``, and ``label`` keys.
    """
    steps: list[dict[str, Any]] = []
    step_num = 1

    safe_name = dashboard_name.lower().replace(" ", "_")

    # 1. Safety snapshot
    steps.append({
        "step": step_num,
        "tool": "odoo_snapshot_create",
        "params": {
            "db_name": db_name,
            "name": f"before_dashboard_{safe_name}",
            "description": f"Safety snapshot before creating dashboard '{dashboard_name}'",
        },
        "description": "Create safety snapshot",
    })
    step_num += 1

    # 2. Create an action window for each metric
    for metric in metrics:
        model = metric["model"]
        measure = metric["measure"]
        label = metric.get("label", measure)
        steps.append({
            "step": step_num,
            "tool": "odoo_record_create",
            "params": {
                "db_name": db_name,
                "model": "ir.actions.act_window",
                "values": {
                    "name": f"{dashboard_name} - {label}",
                    "res_model": model,
                    "view_mode": "graph,pivot,tree",
                    "context": f"{{'graph_measure': '{measure}', 'graph_mode': 'bar'}}",
                },
            },
            "description": f"Create action for metric: {label}",
        })
        step_num += 1

    # 3. Create a parent menu item for the dashboard
    steps.append({
        "step": step_num,
        "tool": "odoo_record_create",
        "params": {
            "db_name": db_name,
            "model": "ir.ui.menu",
            "values": {
                "name": dashboard_name,
            },
        },
        "description": f"Create top-level menu '{dashboard_name}'",
    })
    step_num += 1

    # 4. Create child menu items linking to each action
    for i, metric in enumerate(metrics):
        label = metric.get("label", metric["measure"])
        steps.append({
            "step": step_num,
            "tool": "odoo_record_create",
            "params": {
                "db_name": db_name,
                "model": "ir.ui.menu",
                "values": {
                    "name": label,
                    "action": f"ir.actions.act_window,<action_id_from_step_{i + 2}>",
                },
            },
            "description": f"Create menu item for metric: {label}",
        })
        step_num += 1

    # 5. Health check
    steps.append({
        "step": step_num,
        "tool": "odoo_diagnostics_health_check",
        "params": {"db_name": db_name},
        "description": "Run health check to verify dashboard setup",
    })

    return {
        "workflow": "create_dashboard",
        "dashboard_name": dashboard_name,
        "db_name": db_name,
        "steps": steps,
        "summary": {
            "total_steps": len(steps),
            "metrics_count": len(metrics),
            "actions_created": len(metrics),
            "menu_items_created": 1 + len(metrics),
        },
        "dry_run": dry_run,
    }
