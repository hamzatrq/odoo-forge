"""Healthcare / Medical Practice blueprint — stub."""

from __future__ import annotations

from typing import Any

HEALTHCARE_BLUEPRINT: dict[str, Any] = {
    "name": "Healthcare / Medical Practice",
    "description": (
        "Medical practice or clinic management with patient contacts, "
        "appointment scheduling, billing, and basic inventory for "
        "medical supplies."
    ),
    "modules": [
        "contacts",
        "calendar",
        "account",
        "stock",
        "purchase",
        "hr",
        "mail",
        "project",
    ],
    "optional_modules": [
        {"module": "hr_holidays", "when": "staff leave management"},
        {"module": "hr_expense", "when": "expense tracking for practitioners"},
        {"module": "website", "when": "patient portal or clinic website"},
        {"module": "hr_attendance", "when": "staff attendance tracking"},
    ],
    "models": [],
    "automations": [],
    "settings": {},
    "sample_data": {},
}
