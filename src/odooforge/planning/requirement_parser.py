"""Requirement parser — extract Odoo requirements from natural language."""
from __future__ import annotations
from typing import Any
from odooforge.knowledge import get_knowledge_base


def analyze_requirements(description: str) -> dict[str, Any]:
    """Parse a business description into structured Odoo requirements.

    Uses keyword matching against the knowledge base. No LLM calls.
    """
    kb = get_knowledge_base()
    desc_lower = description.lower()

    # 1. Match industry blueprint
    matched_blueprint = _match_blueprint(desc_lower, kb)

    # 2. Find needed modules
    modules_needed = _match_modules(desc_lower, kb)

    # 3. Detect custom requirements
    custom_requirements = _detect_custom_requirements(desc_lower, kb)

    # 4. Detect infrastructure needs
    infrastructure = _detect_infrastructure(desc_lower)

    # 5. Identify gaps and questions
    questions = _generate_questions(desc_lower, modules_needed, infrastructure)

    # If we matched a blueprint, merge its modules
    if matched_blueprint:
        bp = kb.get_blueprint(matched_blueprint)
        if bp:
            for mod in bp["modules"]:
                if not any(m["module"] == mod for m in modules_needed):
                    mod_info = kb.get_modules().get(mod, {})
                    modules_needed.append({
                        "module": mod,
                        "reason": f"Part of {matched_blueprint} blueprint",
                        "name": mod_info.get("name", mod),
                    })

    return {
        "industry": matched_blueprint,
        "matching_blueprint": matched_blueprint,
        "modules_needed": modules_needed,
        "custom_requirements": custom_requirements,
        "infrastructure": infrastructure,
        "questions_for_user": questions,
    }


def _match_blueprint(desc: str, kb) -> str | None:
    """Find the best matching industry blueprint."""
    # Direct industry name matching
    industry_keywords = {
        "bakery": ["bakery", "pastry", "bread", "cake", "baking"],
        "restaurant": ["restaurant", "food service", "dining", "cafe", "catering", "kitchen"],
        "ecommerce": ["ecommerce", "e-commerce", "online store", "online shop", "web store", "online selling"],
        "manufacturing": ["manufacturing", "factory", "production", "assembly", "fabrication"],
        "services": ["consulting", "professional services", "agency", "freelance", "service company"],
        "retail": ["retail", "shop", "store", "boutique", "merchandise"],
        "healthcare": ["healthcare", "clinic", "hospital", "medical", "dental", "pharmacy"],
        "education": ["education", "school", "training", "academy", "institute", "university", "courses"],
        "real_estate": ["real estate", "property", "rental", "lease", "landlord", "tenant"],
    }

    best_match = None
    best_score = 0

    for blueprint_id, keywords in industry_keywords.items():
        score = sum(1 for kw in keywords if kw in desc)
        if score > best_score:
            best_score = score
            best_match = blueprint_id

    return best_match if best_score > 0 else None


def _match_modules(desc: str, kb) -> list[dict]:
    """Find Odoo modules matching the business description."""
    modules = kb.get_modules()
    matched = []

    for mod_key, mod_info in modules.items():
        score = 0
        reason = ""

        # Check business_needs keywords
        for need in mod_info.get("business_needs", []):
            if need.lower() in desc:
                score += 3
                reason = need

        # Check name
        if mod_info.get("name", "").lower() in desc:
            score += 2
            reason = reason or mod_info["name"]

        # Check business_description keywords
        desc_words = set(desc.split())
        mod_desc_words = set(mod_info.get("business_description", "").lower().split())
        overlap = desc_words & mod_desc_words
        # Filter common words
        meaningful_overlap = overlap - {"a", "an", "the", "and", "or", "for", "with", "to", "of", "in", "on", "is", "are", "was", "were", "be", "been", "has", "have", "had", "do", "does", "did", "will", "would", "can", "could", "should", "may", "might", "shall", "must", "that", "this", "it", "its", "from", "by", "at", "as", "not", "but", "if", "all", "each", "every", "any", "some", "no"}
        if len(meaningful_overlap) >= 2:
            score += 1

        if score > 0:
            matched.append({
                "module": mod_key,
                "name": mod_info.get("name", mod_key),
                "reason": reason or "keyword match",
                "score": score,
            })

    # Sort by score descending, deduplicate
    matched.sort(key=lambda m: m["score"], reverse=True)

    # Remove score from output
    for m in matched:
        del m["score"]

    return matched


def _detect_custom_requirements(desc: str, kb) -> list[dict]:
    """Detect custom field/model needs from the description."""
    patterns = kb.get_patterns()
    requirements = []

    # Pattern-based detection
    pattern_triggers = {
        "partner_extension": ["customer field", "contact field", "loyalty", "tier", "customer category", "customer tag"],
        "product_extension": ["product field", "allergen", "ingredient", "product attribute", "product category", "custom product"],
        "automated_workflow": ["automatic", "automatically", "notification", "alert", "reminder", "trigger", "when"],
        "custom_report": ["report", "pdf", "printout", "certificate", "label"],
        "kanban_workflow": ["pipeline", "stage", "kanban", "workflow", "status"],
        "data_import_pipeline": ["import", "migrate", "csv", "spreadsheet", "existing data"],
    }

    for pattern_id, triggers in pattern_triggers.items():
        matched_triggers = [t for t in triggers if t in desc]
        if matched_triggers:
            pattern = patterns.get(pattern_id, {})
            requirements.append({
                "type": "feature",
                "pattern": pattern_id,
                "description": pattern.get("description", ""),
                "approach": pattern.get("approach", "configuration"),
                "matched_keywords": matched_triggers,
            })

    return requirements


def _detect_infrastructure(desc: str) -> dict[str, Any]:
    """Detect infrastructure needs from the description."""
    import re

    # Multi-company / multi-location detection
    multi_location = False
    locations = 0

    location_patterns = [
        r"(\d+)\s*(?:location|branch|store|shop|outlet|office|warehouse)s?",
        r"(?:location|branch|store|shop|outlet|office|warehouse)s?\s*.*?(\d+)",
        r"multiple\s+(?:location|branch|store|shop|outlet|office|warehouse)s?",
        r"multi[- ](?:location|branch|store|company)",
    ]

    for pattern in location_patterns:
        match = re.search(pattern, desc)
        if match:
            multi_location = True
            groups = match.groups()
            for g in groups:
                if g and g.isdigit():
                    locations = max(locations, int(g))
            break

    # Online/website detection
    needs_website = any(kw in desc for kw in [
        "online", "website", "web store", "ecommerce", "e-commerce",
        "internet", "digital", "web presence",
    ])

    # Delivery detection
    needs_delivery = any(kw in desc for kw in [
        "delivery", "shipping", "ship", "courier", "logistics",
    ])

    return {
        "multi_company": multi_location,
        "locations": locations,
        "needs_website": needs_website,
        "needs_delivery": needs_delivery,
        "needs_code_generation": False,  # Updated by custom requirements analysis
    }


def _generate_questions(desc: str, modules: list, infrastructure: dict) -> list[str]:
    """Generate clarifying questions based on gaps in the description."""
    questions = []

    # Check for missing critical info
    if infrastructure.get("needs_website") and not any(
        m["module"] in ("website_sale", "payment") for m in modules
    ):
        questions.append("Which payment provider would you like for online sales? (e.g., Stripe, PayPal)")

    if infrastructure.get("multi_company") and infrastructure.get("locations", 0) > 1:
        questions.append("Should the locations share inventory or have separate stock?")

    # Check if we have enough info about the business
    module_categories = {m.get("module", "") for m in modules}
    if not any(m in module_categories for m in ("account", "sale", "purchase")):
        questions.append("How do you handle finances? Do you need invoicing, accounting, or both?")

    if not any(m in module_categories for m in ("hr", "hr_attendance")):
        if any(kw in desc for kw in ["employee", "staff", "team", "worker"]):
            questions.append("What HR features do you need? (attendance, time off, expenses, recruitment)")

    return questions
