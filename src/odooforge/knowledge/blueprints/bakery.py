"""Bakery / Artisan Food Producer blueprint — fully detailed."""

from __future__ import annotations

from typing import Any

BAKERY_BLUEPRINT: dict[str, Any] = {
    "name": "Bakery / Artisan Food Producer",
    "description": (
        "Complete Odoo setup for a bakery or artisan food production business. "
        "Covers point-of-sale retail, production planning with recipes (BoM), "
        "ingredient purchasing, inventory tracking with expiry dates, and "
        "optional eCommerce for online orders."
    ),

    # -- Modules -----------------------------------------------------------
    "modules": [
        "point_of_sale",
        "pos_restaurant",
        "mrp",
        "stock",
        "purchase",
        "account",
        "contacts",
        "product",
        "hr",
        "hr_attendance",
        "loyalty",
    ],
    "optional_modules": [
        {"module": "website_sale", "when": "online ordering / delivery"},
        {"module": "website_sale_stock", "when": "show stock availability online"},
        {"module": "delivery", "when": "delivery service"},
        {"module": "quality_control", "when": "formal quality checks required"},
        {"module": "mrp_workorder", "when": "detailed work-center routing"},
        {"module": "maintenance", "when": "equipment maintenance tracking"},
    ],

    # -- Models (extend existing) ------------------------------------------
    "models": [
        {
            "action": "extend",
            "model": "res.partner",
            "fields": [
                {
                    "name": "x_loyalty_tier",
                    "type": "Selection",
                    "selection": [("bronze", "Bronze"), ("silver", "Silver"), ("gold", "Gold")],
                    "string": "Loyalty Tier",
                },
                {"name": "x_loyalty_points", "type": "Integer", "string": "Loyalty Points"},
                {"name": "x_dietary_notes", "type": "Text", "string": "Dietary Notes"},
            ],
        },
        {
            "action": "extend",
            "model": "product.template",
            "fields": [
                {"name": "x_allergens", "type": "Char", "string": "Allergens", "help": "Comma-separated list: gluten, dairy, eggs, nuts, soy"},
                {"name": "x_prep_time_minutes", "type": "Integer", "string": "Prep Time (min)"},
                {"name": "x_is_made_to_order", "type": "Boolean", "string": "Made to Order"},
                {"name": "x_shelf_life_days", "type": "Integer", "string": "Shelf Life (days)"},
            ],
        },
    ],

    # -- Automated actions -------------------------------------------------
    "automations": [
        {
            "name": "Update Loyalty Tier",
            "trigger": "on_write",
            "model": "res.partner",
            "trigger_field": "x_loyalty_points",
            "action": (
                "When x_loyalty_points changes, recalculate x_loyalty_tier: "
                "bronze < 100, silver 100-499, gold >= 500."
            ),
        },
        {
            "name": "Low Stock Alert",
            "trigger": "on_write",
            "model": "stock.quant",
            "action": (
                "When stock quantity drops below reorder minimum, "
                "create an activity for the purchasing manager."
            ),
        },
        {
            "name": "Welcome Email",
            "trigger": "on_create",
            "model": "res.partner",
            "action": (
                "Send a welcome email to new customers with bakery info "
                "and loyalty programme details."
            ),
        },
    ],

    # -- Settings ----------------------------------------------------------
    "settings": {
        "multi_company": False,
        "multi_currency": False,
        "pos_config": {
            "is_loyalty_program": True,
        },
    },

    # -- Sample data -------------------------------------------------------
    "sample_data": {
        "product_categories": [
            {"name": "Breads", "parent": None},
            {"name": "Pastries", "parent": None},
            {"name": "Cakes", "parent": None},
            {"name": "Cookies", "parent": None},
            {"name": "Ingredients", "parent": None},
            {"name": "Flour", "parent": "Ingredients"},
            {"name": "Dairy", "parent": "Ingredients"},
            {"name": "Sweeteners", "parent": "Ingredients"},
        ],
        "products": [
            {
                "name": "Sourdough Loaf",
                "type": "product",
                "category": "Breads",
                "list_price": 6.50,
                "standard_price": 1.80,
                "uom": "Units",
            },
            {
                "name": "Croissant",
                "type": "product",
                "category": "Pastries",
                "list_price": 3.50,
                "standard_price": 0.90,
                "uom": "Units",
            },
            {
                "name": "Chocolate Cake (whole)",
                "type": "product",
                "category": "Cakes",
                "list_price": 35.00,
                "standard_price": 12.00,
                "uom": "Units",
            },
            {
                "name": "Baguette",
                "type": "product",
                "category": "Breads",
                "list_price": 4.00,
                "standard_price": 1.20,
                "uom": "Units",
            },
            {
                "name": "Bread Flour (25kg)",
                "type": "product",
                "category": "Flour",
                "list_price": 0.0,
                "standard_price": 18.50,
                "uom": "kg",
            },
            {
                "name": "Butter (unsalted, 5kg)",
                "type": "product",
                "category": "Dairy",
                "list_price": 0.0,
                "standard_price": 22.00,
                "uom": "kg",
            },
            {
                "name": "Granulated Sugar (25kg)",
                "type": "product",
                "category": "Sweeteners",
                "list_price": 0.0,
                "standard_price": 15.00,
                "uom": "kg",
            },
        ],
        "boms": [
            {
                "product": "Sourdough Loaf",
                "quantity": 10,
                "components": [
                    {"product": "Bread Flour (25kg)", "quantity": 6.0, "uom": "kg"},
                    {"product": "Water", "quantity": 4.0, "uom": "litre"},
                    {"product": "Salt", "quantity": 0.12, "uom": "kg"},
                    {"product": "Sourdough Starter", "quantity": 0.6, "uom": "kg"},
                ],
            },
            {
                "product": "Croissant",
                "quantity": 20,
                "components": [
                    {"product": "Bread Flour (25kg)", "quantity": 2.5, "uom": "kg"},
                    {"product": "Butter (unsalted, 5kg)", "quantity": 1.5, "uom": "kg"},
                    {"product": "Granulated Sugar (25kg)", "quantity": 0.3, "uom": "kg"},
                    {"product": "Milk", "quantity": 0.6, "uom": "litre"},
                    {"product": "Yeast", "quantity": 0.05, "uom": "kg"},
                    {"product": "Salt", "quantity": 0.05, "uom": "kg"},
                    {"product": "Eggs", "quantity": 2, "uom": "Units"},
                ],
            },
        ],
    },

    # -- Multi-location notes ----------------------------------------------
    "multi_location_notes": (
        "For multi-location bakeries, configure one warehouse per location "
        "with inter-warehouse transfers for ingredient sharing. Use the POS "
        "multi-store feature to track sales per location."
    ),
}
