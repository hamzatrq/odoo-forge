"""Restaurant / Food Service blueprint — stub."""

from __future__ import annotations

from typing import Any

RESTAURANT_BLUEPRINT: dict[str, Any] = {
    "name": "Restaurant / Food Service",
    "description": (
        "Full restaurant setup with POS floor plans, table management, "
        "kitchen printing, inventory for ingredients, and staff scheduling."
    ),
    "modules": [
        "point_of_sale",
        "pos_restaurant",
        "stock",
        "purchase",
        "account",
        "contacts",
        "hr",
        "hr_attendance",
    ],
    "optional_modules": [
        {"module": "website", "when": "online presence or reservations"},
        {"module": "loyalty", "when": "customer loyalty programme"},
        {"module": "hr_holidays", "when": "staff leave management"},
        {"module": "quality_control", "when": "food safety checks"},
    ],
    "models": [],
    "automations": [],
    "settings": {
        "pos_config": {
            "is_table_management": True,
            "is_order_printer": True,
        },
    },
    "sample_data": {},
}
