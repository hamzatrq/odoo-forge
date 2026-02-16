"""Professional Services / Consulting blueprint — stub."""

from __future__ import annotations

from typing import Any

SERVICES_BLUEPRINT: dict[str, Any] = {
    "name": "Professional Services / Consulting",
    "description": (
        "Project-based service company with timesheet billing, CRM "
        "pipeline, project management, expense tracking, and "
        "time-and-materials invoicing."
    ),
    "modules": [
        "project",
        "hr_timesheet",
        "sale_timesheet",
        "sale",
        "crm",
        "account",
        "hr_expense",
        "contacts",
        "calendar",
        "mail",
    ],
    "optional_modules": [
        {"module": "hr_holidays", "when": "staff leave management"},
        {"module": "hr_recruitment", "when": "hiring new consultants"},
        {"module": "website", "when": "company website or client portal"},
        {"module": "sale_crm", "when": "link quotations to CRM pipeline"},
    ],
    "models": [],
    "automations": [],
    "settings": {},
    "sample_data": {},
}
