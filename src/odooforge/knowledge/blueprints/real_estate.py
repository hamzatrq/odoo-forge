"""Real Estate / Property Management blueprint — stub."""

from __future__ import annotations

from typing import Any

REAL_ESTATE_BLUEPRINT: dict[str, Any] = {
    "name": "Real Estate / Property Management",
    "description": (
        "Property management with listings as products, CRM pipeline "
        "for leads, contract management, invoicing for rent/fees, and "
        "a website for property listings."
    ),
    "modules": [
        "crm",
        "sale",
        "account",
        "contacts",
        "calendar",
        "website",
        "mail",
        "project",
    ],
    "optional_modules": [
        {"module": "website_sale", "when": "online property listings with booking"},
        {"module": "hr", "when": "agent and staff management"},
        {"module": "hr_expense", "when": "agent expense tracking"},
        {"module": "sale_crm", "when": "link deals to CRM pipeline"},
    ],
    "models": [],
    "automations": [],
    "settings": {},
    "sample_data": {},
}
