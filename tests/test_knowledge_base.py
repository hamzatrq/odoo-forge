"""Tests for the OdooForge domain knowledge base."""

from __future__ import annotations

import pytest

from odooforge.knowledge import KnowledgeBase
from odooforge.knowledge.modules import MODULES
from odooforge.knowledge.dictionary import DICTIONARY
from odooforge.knowledge.patterns import PATTERNS
from odooforge.knowledge.best_practices import BEST_PRACTICES
from odooforge.knowledge.blueprints import BLUEPRINTS


# ── KnowledgeBase loader ─────────────────────────────────────────


class TestKnowledgeBase:
    """Test the central KnowledgeBase loader class."""

    def test_loader_instantiates(self) -> None:
        kb = KnowledgeBase()
        assert kb is not None

    def test_has_modules(self) -> None:
        kb = KnowledgeBase()
        modules = kb.get_modules()
        assert isinstance(modules, dict)
        assert len(modules) > 0

    def test_has_dictionary(self) -> None:
        kb = KnowledgeBase()
        dictionary = kb.get_dictionary()
        assert isinstance(dictionary, dict)
        assert len(dictionary) > 0

    def test_has_patterns(self) -> None:
        kb = KnowledgeBase()
        patterns = kb.get_patterns()
        assert isinstance(patterns, dict)
        assert len(patterns) > 0

    def test_has_best_practices(self) -> None:
        kb = KnowledgeBase()
        bp = kb.get_best_practices()
        assert isinstance(bp, dict)
        assert "rules" in bp
        assert len(bp["rules"]) > 0

    def test_has_blueprints(self) -> None:
        kb = KnowledgeBase()
        bp_list = kb.list_blueprints()
        assert isinstance(bp_list, list)
        assert len(bp_list) > 0

    def test_get_blueprint_by_id(self) -> None:
        kb = KnowledgeBase()
        bakery = kb.get_blueprint("bakery")
        assert bakery is not None
        assert bakery["name"] == "Bakery / Artisan Food Producer"

    def test_get_unknown_blueprint_returns_none(self) -> None:
        kb = KnowledgeBase()
        result = kb.get_blueprint("nonexistent_industry")
        assert result is None


# ── Modules knowledge ────────────────────────────────────────────


class TestModulesKnowledge:
    """Validate the MODULES catalog structure and content."""

    def test_structure_validation(self) -> None:
        """Every module entry must have the required keys."""
        required_keys = {"name", "business_description", "category", "depends", "business_needs"}
        for module_id, info in MODULES.items():
            missing = required_keys - set(info.keys())
            assert not missing, f"Module '{module_id}' missing keys: {missing}"

    def test_known_modules_present(self) -> None:
        """Check that key modules are in the catalog."""
        expected = [
            "sale", "crm", "sale_crm", "purchase", "account",
            "account_payment", "stock", "stock_account", "delivery",
            "mrp", "mrp_workorder", "quality_control", "maintenance",
            "point_of_sale", "pos_restaurant", "pos_sale", "loyalty",
            "website", "website_sale", "website_sale_stock",
            "website_sale_wishlist", "website_sale_comparison", "payment",
            "hr", "hr_holidays", "hr_attendance", "hr_expense",
            "hr_recruitment", "hr_timesheet", "project", "sale_timesheet",
            "mail", "calendar", "contacts", "product",
        ]
        for mod in expected:
            assert mod in MODULES, f"Expected module '{mod}' not found in MODULES"

    def test_business_description_quality(self) -> None:
        """Business descriptions should be non-trivial strings."""
        for module_id, info in MODULES.items():
            desc = info["business_description"]
            assert isinstance(desc, str), f"Module '{module_id}' description is not a string"
            assert len(desc) >= 30, (
                f"Module '{module_id}' description too short ({len(desc)} chars): {desc!r}"
            )

    def test_count_at_least_30(self) -> None:
        """Must have at least 30 modules (spec says 35+)."""
        assert len(MODULES) >= 30, f"Only {len(MODULES)} modules, need at least 30"

    def test_depends_is_list(self) -> None:
        """The depends field must always be a list."""
        for module_id, info in MODULES.items():
            assert isinstance(info["depends"], list), (
                f"Module '{module_id}' depends is not a list"
            )

    def test_business_needs_is_list(self) -> None:
        """The business_needs field must be a non-empty list."""
        for module_id, info in MODULES.items():
            needs = info["business_needs"]
            assert isinstance(needs, list), f"Module '{module_id}' business_needs is not a list"
            assert len(needs) > 0, f"Module '{module_id}' has empty business_needs"


# ── Dictionary knowledge ─────────────────────────────────────────


class TestDictionaryKnowledge:
    """Validate the DICTIONARY structure and coverage."""

    def test_structure_validation(self) -> None:
        """Every dictionary entry must have the required keys."""
        required_keys = {"model", "filter", "description", "tips"}
        for term, info in DICTIONARY.items():
            missing = required_keys - set(info.keys())
            assert not missing, f"Term '{term}' missing keys: {missing}"

    def test_common_terms_present(self) -> None:
        """Check that common business terms are mapped."""
        expected_terms = [
            "customer", "vendor", "supplier", "contact", "company",
            "employee", "department", "user",
            "sales order", "quotation", "order line",
            "purchase order", "rfq",
            "invoice", "bill", "credit note", "payment", "journal", "account", "tax",
            "product", "product variant", "product category", "price list",
            "warehouse", "stock location", "delivery order", "receipt", "stock move",
            "bill of materials", "bom", "manufacturing order", "work center", "work order",
            "lead", "opportunity", "pipeline stage", "sales team",
            "project", "task", "task stage",
            "leave request", "expense", "job position", "applicant",
            "pos order", "pos session",
            "currency", "country", "sequence", "attachment", "activity",
            "email template", "automated action", "scheduled action",
            "access rule", "record rule", "security group",
        ]
        for term in expected_terms:
            assert term in DICTIONARY, f"Expected term '{term}' not found in DICTIONARY"

    def test_count_at_least_40(self) -> None:
        """Must have at least 40 terms (spec says 60+)."""
        assert len(DICTIONARY) >= 40, f"Only {len(DICTIONARY)} terms, need at least 40"

    def test_model_is_dotted_name(self) -> None:
        """Every model value should look like an Odoo model (contains a dot)."""
        for term, info in DICTIONARY.items():
            model = info["model"]
            assert "." in model, f"Term '{term}' model '{model}' does not look like an Odoo model"

    def test_filter_is_list(self) -> None:
        """The filter field must be a list."""
        for term, info in DICTIONARY.items():
            assert isinstance(info["filter"], list), (
                f"Term '{term}' filter is not a list"
            )


# ── Patterns knowledge ───────────────────────────────────────────


class TestPatternsKnowledge:
    """Validate the PATTERNS structure and content."""

    def test_structure_validation(self) -> None:
        """Every pattern must have the required keys."""
        required_keys = {"name", "description", "approach", "when_to_use", "ingredients"}
        for pattern_id, info in PATTERNS.items():
            missing = required_keys - set(info.keys())
            assert not missing, f"Pattern '{pattern_id}' missing keys: {missing}"

    def test_known_patterns_present(self) -> None:
        """Check that all specified patterns are included."""
        expected = [
            "partner_extension", "product_extension",
            "trackable_custom_model", "simple_custom_model",
            "multi_company_model", "smart_button",
            "automated_workflow", "custom_report",
            "kanban_workflow", "approval_workflow",
            "data_import_pipeline", "scheduled_job",
            "website_controller",
        ]
        for pat in expected:
            assert pat in PATTERNS, f"Expected pattern '{pat}' not found in PATTERNS"

    def test_approach_values_valid(self) -> None:
        """The approach field must be one of the allowed values."""
        valid_approaches = {"configuration", "code_generation", "either"}
        for pattern_id, info in PATTERNS.items():
            assert info["approach"] in valid_approaches, (
                f"Pattern '{pattern_id}' has invalid approach: {info['approach']}"
            )

    def test_count_at_least_10(self) -> None:
        """Must have at least 10 patterns (spec says 13+)."""
        assert len(PATTERNS) >= 10, f"Only {len(PATTERNS)} patterns, need at least 10"

    def test_ingredients_is_list(self) -> None:
        """Ingredients must be a non-empty list."""
        for pattern_id, info in PATTERNS.items():
            ingredients = info["ingredients"]
            assert isinstance(ingredients, list), (
                f"Pattern '{pattern_id}' ingredients is not a list"
            )
            assert len(ingredients) > 0, (
                f"Pattern '{pattern_id}' has empty ingredients"
            )


# ── Best practices knowledge ─────────────────────────────────────


class TestBestPracticesKnowledge:
    """Validate the BEST_PRACTICES structure and content."""

    def test_structure_validation(self) -> None:
        """Top-level must have a 'rules' key with a list."""
        assert "rules" in BEST_PRACTICES
        assert isinstance(BEST_PRACTICES["rules"], list)

    def test_rules_list_exists(self) -> None:
        """Rules list must be non-empty."""
        assert len(BEST_PRACTICES["rules"]) > 0

    def test_rule_structure(self) -> None:
        """Every rule must have the required keys."""
        required_keys = {"category", "rule", "why", "example"}
        for i, rule in enumerate(BEST_PRACTICES["rules"]):
            missing = required_keys - set(rule.keys())
            assert not missing, f"Rule #{i} missing keys: {missing}"

    def test_count_at_least_10(self) -> None:
        """Must have at least 10 rules (spec says 22+)."""
        assert len(BEST_PRACTICES["rules"]) >= 10, (
            f"Only {len(BEST_PRACTICES['rules'])} rules, need at least 10"
        )

    def test_category_coverage(self) -> None:
        """Rules should cover multiple categories."""
        categories = {rule["category"] for rule in BEST_PRACTICES["rules"]}
        expected_categories = {
            "naming", "model_design", "fields", "security", "views",
            "automation", "reports", "performance",
        }
        missing = expected_categories - categories
        assert not missing, f"Missing rule categories: {missing}"

    def test_rule_text_quality(self) -> None:
        """Rule text and why should be non-trivial."""
        for i, rule in enumerate(BEST_PRACTICES["rules"]):
            assert len(rule["rule"]) >= 10, f"Rule #{i} text too short"
            assert len(rule["why"]) >= 20, f"Rule #{i} 'why' too short"


# ── Blueprints knowledge ─────────────────────────────────────────


class TestBlueprintsKnowledge:
    """Validate the blueprint registry and individual blueprints."""

    def test_registry_has_9_blueprints(self) -> None:
        """Must have exactly 9 industry blueprints."""
        assert len(BLUEPRINTS) == 9, f"Expected 9 blueprints, got {len(BLUEPRINTS)}"

    def test_registry_ids(self) -> None:
        """Check that all expected blueprint IDs are present."""
        expected_ids = {
            "bakery", "restaurant", "ecommerce", "manufacturing",
            "services", "retail", "healthcare", "education", "real_estate",
        }
        assert set(BLUEPRINTS.keys()) == expected_ids

    def test_structure_validation_per_blueprint(self) -> None:
        """Every blueprint must have the required top-level keys."""
        required_keys = {
            "name", "description", "modules", "optional_modules",
            "models", "automations", "settings", "sample_data",
        }
        for bp_id, bp in BLUEPRINTS.items():
            missing = required_keys - set(bp.keys())
            assert not missing, f"Blueprint '{bp_id}' missing keys: {missing}"

    def test_modules_is_list(self) -> None:
        """modules and optional_modules must be lists."""
        for bp_id, bp in BLUEPRINTS.items():
            assert isinstance(bp["modules"], list), (
                f"Blueprint '{bp_id}' modules is not a list"
            )
            assert isinstance(bp["optional_modules"], list), (
                f"Blueprint '{bp_id}' optional_modules is not a list"
            )
            assert len(bp["modules"]) > 0, (
                f"Blueprint '{bp_id}' has empty modules list"
            )

    def test_bakery_completeness(self) -> None:
        """Bakery blueprint must be fully detailed — not a stub."""
        bakery = BLUEPRINTS["bakery"]

        # Has modules
        assert len(bakery["modules"]) >= 5
        assert len(bakery["optional_modules"]) >= 3

        # Has model extensions with field-level detail
        assert len(bakery["models"]) >= 2
        for model in bakery["models"]:
            assert "model" in model
            assert "fields" in model
            assert len(model["fields"]) >= 3

        # Has automations
        assert len(bakery["automations"]) >= 2
        for auto in bakery["automations"]:
            assert "name" in auto
            assert "trigger" in auto
            assert "model" in auto

        # Has settings
        assert len(bakery["settings"]) >= 2

        # Has sample data
        assert len(bakery["sample_data"]) >= 2
        assert "products" in bakery["sample_data"]
        assert len(bakery["sample_data"]["products"]) >= 3

    def test_bakery_blueprint_has_model_extensions(self) -> None:
        """Bakery blueprint should extend res.partner and product.template."""
        bakery = BLUEPRINTS["bakery"]
        # Should extend res.partner and product.template
        model_targets = [m["model"] for m in bakery["models"]]
        assert "res.partner" in model_targets
        assert "product.template" in model_targets

    def test_bakery_has_boms(self) -> None:
        """Bakery blueprint should include sample Bill of Materials."""
        bakery = BLUEPRINTS["bakery"]
        assert "boms" in bakery["sample_data"]
        assert len(bakery["sample_data"]["boms"]) >= 1

    def test_stub_blueprints_have_modules(self) -> None:
        """Even stub blueprints must have a non-empty modules list."""
        stubs = ["restaurant", "ecommerce", "manufacturing", "services",
                 "retail", "healthcare", "education", "real_estate"]
        for bp_id in stubs:
            bp = BLUEPRINTS[bp_id]
            assert len(bp["modules"]) >= 3, (
                f"Stub blueprint '{bp_id}' has fewer than 3 modules"
            )
