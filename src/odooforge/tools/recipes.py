"""Recipe engine — pre-built industry setup recipes for common Odoo configurations."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC

logger = logging.getLogger(__name__)


# ── Recipe Definitions ────────────────────────────────────────────

RECIPES: dict[str, dict[str, Any]] = {
    "restaurant": {
        "name": "Restaurant / Food Service",
        "description": "Full restaurant setup with POS, inventory, and kitchen management.",
        "modules": [
            "point_of_sale", "pos_restaurant", "stock", "purchase",
            "account", "contacts", "hr", "hr_attendance",
        ],
        "settings": {
            "pos_config": {
                "is_table_management": True,
                "is_order_printer": True,
            },
        },
        "steps": [
            {"action": "install_modules", "description": "Install POS, inventory, purchasing, HR"},
            {"action": "configure_pos", "description": "Enable table management and kitchen printing"},
            {"action": "create_product_categories", "description": "Create Food, Beverages, Desserts categories",
             "data": [
                 {"model": "product.category", "values": {"name": "Food"}},
                 {"model": "product.category", "values": {"name": "Beverages"}},
                 {"model": "product.category", "values": {"name": "Desserts"}},
             ]},
        ],
        "post_setup": "Configure your menu items, set up printers for kitchen/bar, and create employee PINs.",
    },
    "ecommerce": {
        "name": "eCommerce Store",
        "description": "Online store with website, products, payments, and shipping.",
        "modules": [
            "website_sale", "website_sale_stock", "payment",
            "delivery", "stock", "account", "contacts", "crm",
            "website_sale_wishlist", "website_sale_comparison",
        ],
        "settings": {
            "website_sale": {
                "enabled_buy_button": True,
            },
        },
        "steps": [
            {"action": "install_modules", "description": "Install eCommerce, payments, delivery, CRM"},
            {"action": "configure_website", "description": "Enable shop page with cart and checkout"},
            {"action": "setup_payment", "description": "Guide: Configure payment providers (Stripe/PayPal)"},
        ],
        "post_setup": "Add products with images, configure shipping methods, and set up payment providers.",
    },
    "manufacturing": {
        "name": "Manufacturing / Production",
        "description": "Production with BoM, work orders, quality control, and MRP.",
        "modules": [
            "mrp", "mrp_workorder", "quality_control", "stock",
            "purchase", "sale", "account", "maintenance",
        ],
        "settings": {},
        "steps": [
            {"action": "install_modules", "description": "Install MRP, quality, maintenance, purchasing"},
            {"action": "configure_warehouse", "description": "Set up manufacturing warehouse and locations"},
            {"action": "create_work_centers", "description": "Guide: Create production work centers",
             "data": [
                 {"model": "mrp.workcenter", "values": {"name": "Assembly Line", "time_efficiency": 100}},
                 {"model": "mrp.workcenter", "values": {"name": "Quality Check", "time_efficiency": 100}},
             ]},
        ],
        "post_setup": "Create Bills of Materials, define routings, and set reorder rules for raw materials.",
    },
    "services": {
        "name": "Professional Services / Consulting",
        "description": "Project-based service company with timesheets, invoicing, and CRM.",
        "modules": [
            "project", "timesheet_grid", "sale_timesheet",
            "hr_timesheet", "account", "crm", "sale",
            "contacts", "calendar", "mail",
        ],
        "settings": {},
        "steps": [
            {"action": "install_modules", "description": "Install project, timesheets, CRM, sales"},
            {"action": "configure_projects", "description": "Enable timesheet billing on projects"},
            {"action": "create_stages", "description": "Create project stages",
             "data": [
                 {"model": "project.task.type", "values": {"name": "Backlog"}},
                 {"model": "project.task.type", "values": {"name": "In Progress"}},
                 {"model": "project.task.type", "values": {"name": "Review"}},
                 {"model": "project.task.type", "values": {"name": "Done"}},
             ]},
        ],
        "post_setup": "Create service products, set hourly rates, and configure invoice policies.",
    },
    "retail": {
        "name": "Retail Store",
        "description": "Brick-and-mortar retail with POS, inventory, and loyalty programs.",
        "modules": [
            "point_of_sale", "stock", "purchase", "account",
            "contacts", "loyalty", "pos_sale",
        ],
        "settings": {
            "pos_config": {
                "is_loyalty_program": True,
            },
        },
        "steps": [
            {"action": "install_modules", "description": "Install POS, inventory, purchasing, loyalty"},
            {"action": "configure_pos", "description": "Set up POS with barcode scanning"},
            {"action": "setup_inventory", "description": "Configure reorder rules and stock alerts"},
        ],
        "post_setup": "Import product catalog, set up barcode labels, and configure loyalty programs.",
    },
}


async def odoo_recipe_list() -> dict[str, Any]:
    """List all available industry setup recipes."""
    recipes = []
    for key, recipe in RECIPES.items():
        recipes.append({
            "id": key,
            "name": recipe["name"],
            "description": recipe["description"],
            "modules": recipe["modules"],
            "steps": len(recipe["steps"]),
        })

    return {
        "recipes": recipes,
        "count": len(recipes),
        "message": "Use odoo_recipe_execute with the recipe id to run a recipe.",
    }


async def odoo_recipe_execute(
    rpc: OdooRPC,
    db_name: str,
    recipe_id: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Execute an industry recipe to set up an Odoo instance.

    Args:
        recipe_id: Recipe identifier (e.g., "restaurant", "ecommerce").
        dry_run: If True, only show what would be done without making changes.
    """
    recipe = RECIPES.get(recipe_id)
    if not recipe:
        return {
            "status": "error",
            "message": f"Unknown recipe: {recipe_id}",
            "available": list(RECIPES.keys()),
        }

    if dry_run:
        return {
            "status": "dry_run",
            "recipe": recipe_id,
            "name": recipe["name"],
            "modules_to_install": recipe["modules"],
            "steps": [
                {"step": i + 1, "action": s["action"], "description": s["description"]}
                for i, s in enumerate(recipe["steps"])
            ],
            "post_setup": recipe.get("post_setup", ""),
            "message": f"Dry run for '{recipe['name']}'. Set dry_run=False to execute.",
        }

    # Execute the recipe
    results = []

    # Step 1: Install modules
    installed = rpc.search_read(
        "ir.module.module",
        [["state", "=", "installed"]],
        fields=["name"],
        db=db_name,
    )
    installed_names = {m["name"] for m in installed}
    to_install = [m for m in recipe["modules"] if m not in installed_names]

    if to_install:
        for module_name in to_install:
            try:
                module_ids = rpc.search_read(
                    "ir.module.module",
                    [["name", "=", module_name]],
                    fields=["id", "state"],
                    limit=1,
                    db=db_name,
                )
                if module_ids and module_ids[0]["state"] != "installed":
                    rpc.execute_method(
                        "ir.module.module", "button_immediate_install",
                        [[module_ids[0]["id"]]], db=db_name,
                    )
                    results.append({"module": module_name, "status": "installed"})
                elif module_ids:
                    results.append({"module": module_name, "status": "already_installed"})
                else:
                    results.append({"module": module_name, "status": "not_found"})
            except Exception as e:
                results.append({"module": module_name, "status": "error", "detail": str(e)})
    else:
        results.append({"step": "modules", "status": "all_already_installed"})

    # Step 2: Create data records from recipe steps
    for step in recipe["steps"]:
        if "data" in step:
            for record in step["data"]:
                try:
                    rec_id = rpc.create(
                        record["model"], record["values"], db=db_name,
                    )
                    results.append({
                        "step": step["description"],
                        "model": record["model"],
                        "id": rec_id,
                        "status": "created",
                    })
                except Exception as e:
                    results.append({
                        "step": step["description"],
                        "model": record["model"],
                        "status": "error",
                        "detail": str(e),
                    })

    return {
        "status": "executed",
        "recipe": recipe_id,
        "name": recipe["name"],
        "results": results,
        "post_setup": recipe.get("post_setup", ""),
        "message": f"Recipe '{recipe['name']}' executed. "
                   f"{sum(1 for r in results if r.get('status') in ('installed', 'created'))} "
                   f"actions completed. Review post_setup notes.",
    }
