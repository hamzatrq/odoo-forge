"""Manufacturing / Production blueprint — stub."""

from __future__ import annotations

from typing import Any

MANUFACTURING_BLUEPRINT: dict[str, Any] = {
    "name": "Manufacturing / Production",
    "description": (
        "Production facility with Bills of Materials, work orders, "
        "quality control, equipment maintenance, and MRP planning."
    ),
    "modules": [
        "mrp",
        "mrp_workorder",
        "quality_control",
        "stock",
        "purchase",
        "sale",
        "account",
        "maintenance",
        "contacts",
    ],
    "optional_modules": [
        {"module": "hr", "when": "employee management"},
        {"module": "hr_attendance", "when": "shop floor attendance tracking"},
        {"module": "stock_account", "when": "inventory valuation in accounting"},
        {"module": "delivery", "when": "shipping finished goods"},
    ],
    "models": [],
    "automations": [],
    "settings": {},
    "sample_data": {},
}
