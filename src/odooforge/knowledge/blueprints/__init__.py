"""Industry blueprint registry — aggregates all blueprint modules."""

from __future__ import annotations

from typing import Any

from odooforge.knowledge.blueprints.bakery import BAKERY_BLUEPRINT
from odooforge.knowledge.blueprints.restaurant import RESTAURANT_BLUEPRINT
from odooforge.knowledge.blueprints.ecommerce import ECOMMERCE_BLUEPRINT
from odooforge.knowledge.blueprints.manufacturing import MANUFACTURING_BLUEPRINT
from odooforge.knowledge.blueprints.services import SERVICES_BLUEPRINT
from odooforge.knowledge.blueprints.retail import RETAIL_BLUEPRINT
from odooforge.knowledge.blueprints.healthcare import HEALTHCARE_BLUEPRINT
from odooforge.knowledge.blueprints.education import EDUCATION_BLUEPRINT
from odooforge.knowledge.blueprints.real_estate import REAL_ESTATE_BLUEPRINT

BLUEPRINTS: dict[str, dict[str, Any]] = {
    "bakery": BAKERY_BLUEPRINT,
    "restaurant": RESTAURANT_BLUEPRINT,
    "ecommerce": ECOMMERCE_BLUEPRINT,
    "manufacturing": MANUFACTURING_BLUEPRINT,
    "services": SERVICES_BLUEPRINT,
    "retail": RETAIL_BLUEPRINT,
    "healthcare": HEALTHCARE_BLUEPRINT,
    "education": EDUCATION_BLUEPRINT,
    "real_estate": REAL_ESTATE_BLUEPRINT,
}
