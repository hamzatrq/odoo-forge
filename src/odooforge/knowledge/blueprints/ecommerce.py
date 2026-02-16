"""eCommerce Store blueprint — stub."""

from __future__ import annotations

from typing import Any

ECOMMERCE_BLUEPRINT: dict[str, Any] = {
    "name": "eCommerce Store",
    "description": (
        "Online store with product catalog, shopping cart, payment "
        "processing, shipping integration, and CRM for lead capture."
    ),
    "modules": [
        "website_sale",
        "website_sale_stock",
        "website_sale_wishlist",
        "website_sale_comparison",
        "payment",
        "delivery",
        "stock",
        "account",
        "contacts",
        "crm",
    ],
    "optional_modules": [
        {"module": "loyalty", "when": "customer loyalty programme"},
        {"module": "sale_crm", "when": "link sales to CRM pipeline"},
        {"module": "website_blog", "when": "content marketing blog"},
        {"module": "website_livechat", "when": "live chat support"},
    ],
    "models": [],
    "automations": [],
    "settings": {
        "website_sale": {
            "enabled_buy_button": True,
        },
    },
    "sample_data": {},
}
