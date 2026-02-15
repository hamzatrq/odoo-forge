"""Knowledge base tools — module info, search, community gaps."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC

logger = logging.getLogger(__name__)

# ── Built‑in knowledge data ───────────────────────────────────────

MODULE_KNOWLEDGE: dict[str, dict] = {
    "sale": {
        "name": "Sales",
        "description": "Core sales order management with quotations and invoicing.",
        "models": ["sale.order", "sale.order.line", "sale.order.template"],
        "key_fields": {
            "sale.order": ["partner_id", "date_order", "state", "amount_total",
                          "pricelist_id", "payment_term_id", "team_id"],
        },
        "typical_workflow": "Quotation → Sent → Confirmed → Invoiced → Done",
        "depends": ["contacts", "account"],
        "common_customizations": [
            "Add custom fields for approval workflow",
            "Discount limits per salesperson",
            "Custom PDF report layout",
        ],
    },
    "purchase": {
        "name": "Purchase",
        "description": "Purchase order management and vendor bills.",
        "models": ["purchase.order", "purchase.order.line"],
        "key_fields": {
            "purchase.order": ["partner_id", "date_order", "state", "amount_total"],
        },
        "typical_workflow": "RFQ → Sent → Confirmed → Received → Billed",
        "depends": ["contacts", "account"],
        "common_customizations": [
            "Vendor approval process",
            "Purchase budget limits",
            "Multi-step approval",
        ],
    },
    "account": {
        "name": "Invoicing / Accounting",
        "description": "Full accounting suite with invoicing, payments, and reports.",
        "models": ["account.move", "account.move.line", "account.payment",
                   "account.journal", "account.account"],
        "key_fields": {
            "account.move": ["partner_id", "move_type", "state", "amount_total",
                            "journal_id", "date", "payment_state"],
        },
        "typical_workflow": "Draft → Posted → Paid/Reconciled",
        "depends": ["contacts"],
        "common_customizations": [
            "Custom chart of accounts",
            "Payment follow-up sequences",
            "Tax configuration per region",
        ],
    },
    "stock": {
        "name": "Inventory",
        "description": "Warehouse and inventory management with traceability.",
        "models": ["stock.picking", "stock.move", "stock.warehouse",
                   "stock.location", "stock.quant", "product.product"],
        "key_fields": {
            "stock.picking": ["partner_id", "picking_type_id", "state",
                             "scheduled_date", "origin"],
        },
        "typical_workflow": "Draft → Waiting → Ready → Done",
        "depends": ["product"],
        "common_customizations": [
            "Multi-warehouse routing",
            "Custom lot/serial tracking",
            "Barcode scanning workflows",
        ],
    },
    "crm": {
        "name": "CRM",
        "description": "Customer relationship management with pipeline and activities.",
        "models": ["crm.lead", "crm.team", "crm.stage"],
        "key_fields": {
            "crm.lead": ["partner_id", "stage_id", "team_id", "user_id",
                         "expected_revenue", "probability", "type"],
        },
        "typical_workflow": "New → Qualified → Proposition → Won/Lost",
        "depends": ["contacts", "mail"],
        "common_customizations": [
            "Lead scoring automation",
            "Custom pipeline stages",
            "Integration with external lead sources",
        ],
    },
    "hr": {
        "name": "Employees",
        "description": "Core HR module for employee records and departments.",
        "models": ["hr.employee", "hr.department", "hr.job"],
        "key_fields": {
            "hr.employee": ["name", "department_id", "job_id", "parent_id",
                           "work_email", "work_phone"],
        },
        "typical_workflow": "N/A — master data management",
        "depends": [],
        "common_customizations": [
            "Custom employee fields (badges, certifications)",
            "Department-level access control",
            "Employee onboarding checklist",
        ],
    },
    "project": {
        "name": "Project",
        "description": "Project management with tasks, stages, and timesheets.",
        "models": ["project.project", "project.task", "project.task.type"],
        "key_fields": {
            "project.task": ["project_id", "user_ids", "stage_id", "date_deadline",
                            "priority", "tag_ids"],
        },
        "typical_workflow": "New → In Progress → Review → Done",
        "depends": ["mail"],
        "common_customizations": [
            "Kanban workflow automation",
            "Task templates",
            "Time tracking and billing",
        ],
    },
    "website": {
        "name": "Website Builder",
        "description": "Drag-and-drop website builder with pages, menus, and themes.",
        "models": ["website", "website.page", "website.menu"],
        "key_fields": {},
        "typical_workflow": "Edit → Preview → Publish",
        "depends": [],
        "common_customizations": [
            "Custom theme and branding",
            "Landing page creation",
            "SEO optimization",
        ],
    },
}


async def odoo_knowledge_module_info(
    module_name: str,
) -> dict[str, Any]:
    """Get curated knowledge about an Odoo module — models, fields, workflows.

    Built-in knowledge covers: sale, purchase, account, stock, crm, hr, project, website.
    """
    info = MODULE_KNOWLEDGE.get(module_name)
    if not info:
        available = sorted(MODULE_KNOWLEDGE.keys())
        return {
            "found": False,
            "message": f"No built-in knowledge for '{module_name}'.",
            "available": available,
            "suggestion": "Use odoo_module_info for live module data, "
                         "or odoo_model_fields for field details.",
        }

    return {
        "found": True,
        "module": module_name,
        **info,
    }


async def odoo_knowledge_search(
    query: str,
) -> dict[str, Any]:
    """Search the knowledge base for relevant Odoo information.

    Args:
        query: Search term (e.g., "invoice", "warehouse", "CRM pipeline").
    """
    query_lower = query.lower()
    results = []

    for module_key, info in MODULE_KNOWLEDGE.items():
        score = 0
        if query_lower in module_key:
            score += 10
        if query_lower in info["name"].lower():
            score += 8
        if query_lower in info["description"].lower():
            score += 5
        for model in info.get("models", []):
            if query_lower in model.lower():
                score += 6
        for custom in info.get("common_customizations", []):
            if query_lower in custom.lower():
                score += 3

        if score > 0:
            results.append({
                "module": module_key,
                "name": info["name"],
                "description": info["description"],
                "relevance": score,
            })

    results.sort(key=lambda r: r["relevance"], reverse=True)

    return {
        "query": query,
        "results": results[:10],
        "count": len(results),
        "message": f"Found {len(results)} result(s) for '{query}'." if results
                   else f"No results for '{query}'. Try broader terms.",
    }


async def odoo_knowledge_community_gaps(
    rpc: OdooRPC,
    db_name: str,
) -> dict[str, Any]:
    """Identify gaps between installed modules and recommended configurations.

    Checks for common misconfigurations and missing complementary modules.
    """
    # Get installed modules
    installed = rpc.search_read(
        "ir.module.module",
        [["state", "=", "installed"]],
        fields=["name"],
        db=db_name,
    )
    installed_names = {m["name"] for m in installed}

    recommendations = []

    # Check for common complementary modules
    if "sale" in installed_names and "crm" not in installed_names:
        recommendations.append({
            "type": "module",
            "suggestion": "Install CRM module",
            "reason": "Sales without CRM means no pipeline management. "
                     "Most sales teams benefit from lead tracking.",
        })

    if "account" in installed_names and "sale" not in installed_names:
        recommendations.append({
            "type": "module",
            "suggestion": "Consider Sales module",
            "reason": "Accounting without Sales means manual invoice creation. "
                     "Sales automates the quotation-to-invoice flow.",
        })

    if "stock" in installed_names and "purchase" not in installed_names:
        recommendations.append({
            "type": "module",
            "suggestion": "Install Purchase module",
            "reason": "Inventory without Purchase means manual receipt creation. "
                     "Purchase automates procurement.",
        })

    if "hr" in installed_names and "hr_holidays" not in installed_names:
        recommendations.append({
            "type": "module",
            "suggestion": "Install Time Off module (hr_holidays)",
            "reason": "Most HR setups need leave/absence management.",
        })

    if "website" in installed_names and "website_sale" not in installed_names:
        recommendations.append({
            "type": "module",
            "suggestion": "Consider eCommerce (website_sale)",
            "reason": "Website without eCommerce is a brochure site. "
                     "Add eCommerce for online selling.",
        })

    # Check company configuration
    companies = rpc.search_read(
        "res.company", [], fields=["name", "currency_id", "country_id", "email"],
        limit=1, db=db_name,
    )
    if companies:
        comp = companies[0]
        if not comp.get("email"):
            recommendations.append({
                "type": "config",
                "suggestion": "Set company email",
                "reason": "Company email is used as the default sender for all outgoing mail.",
            })
        if not comp.get("country_id"):
            recommendations.append({
                "type": "config",
                "suggestion": "Set company country",
                "reason": "Country affects tax computation, address formats, and localizations.",
            })

    return {
        "installed_modules": len(installed_names),
        "recommendations": recommendations,
        "count": len(recommendations),
        "message": f"{len(recommendations)} suggestion(s) to improve your setup."
                   if recommendations else "No gaps detected. Setup looks solid!",
    }
