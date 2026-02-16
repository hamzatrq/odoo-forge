"""Education / Training Center blueprint — stub."""

from __future__ import annotations

from typing import Any

EDUCATION_BLUEPRINT: dict[str, Any] = {
    "name": "Education / Training Center",
    "description": (
        "School or training center with student contacts, course "
        "management via projects, scheduling, invoicing, and optional "
        "eCommerce for course enrollment."
    ),
    "modules": [
        "contacts",
        "project",
        "calendar",
        "account",
        "sale",
        "hr",
        "mail",
    ],
    "optional_modules": [
        {"module": "website", "when": "school or training centre website"},
        {"module": "website_sale", "when": "online course enrollment"},
        {"module": "hr_holidays", "when": "staff leave management"},
        {"module": "hr_attendance", "when": "staff attendance tracking"},
        {"module": "hr_expense", "when": "expense tracking for trainers"},
    ],
    "models": [],
    "automations": [],
    "settings": {},
    "sample_data": {},
}
