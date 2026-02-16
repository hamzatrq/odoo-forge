"""Retail Store blueprint — stub."""

from __future__ import annotations

from typing import Any

RETAIL_BLUEPRINT: dict[str, Any] = {
    "name": "Retail Store",
    "description": (
        "Brick-and-mortar retail with POS terminals, barcode scanning, "
        "inventory management, loyalty programs, and optional eCommerce."
    ),
    "modules": [
        "point_of_sale",
        "stock",
        "purchase",
        "account",
        "contacts",
        "loyalty",
        "pos_sale",
    ],
    "optional_modules": [
        {"module": "website_sale", "when": "online store"},
        {"module": "website_sale_stock", "when": "show stock availability online"},
        {"module": "delivery", "when": "shipping / delivery service"},
        {"module": "hr", "when": "employee management"},
        {"module": "hr_attendance", "when": "staff attendance tracking"},
    ],
    "models": [],
    "automations": [],
    "settings": {
        "pos_config": {
            "is_loyalty_program": True,
        },
    },
    "sample_data": {},
}
