"""Tests for the planning tools — requirement analysis, solution design, plan validation."""
import pytest
from typing import Any


class TestAnalyzeRequirements:
    def test_bakery_description_matches_blueprint(self):
        from odooforge.planning.requirement_parser import analyze_requirements
        result = analyze_requirements("I run a bakery with 3 locations and delivery")
        assert result["matching_blueprint"] == "bakery"

    def test_restaurant_description_matches_blueprint(self):
        from odooforge.planning.requirement_parser import analyze_requirements
        result = analyze_requirements("I own a restaurant with dine-in and takeout")
        assert result["matching_blueprint"] == "restaurant"

    def test_ecommerce_description_matches_blueprint(self):
        from odooforge.planning.requirement_parser import analyze_requirements
        result = analyze_requirements("I want to sell products online through an ecommerce store")
        assert result["matching_blueprint"] == "ecommerce"

    def test_no_match_returns_none(self):
        from odooforge.planning.requirement_parser import analyze_requirements
        result = analyze_requirements("something very generic")
        # May or may not match, but shouldn't crash
        assert isinstance(result["matching_blueprint"], (str, type(None)))

    def test_modules_detected_from_keywords(self):
        from odooforge.planning.requirement_parser import analyze_requirements
        result = analyze_requirements("I need to track inventory and manage employee timesheets")
        modules = [m["module"] for m in result["modules_needed"]]
        assert "stock" in modules or "hr_timesheet" in modules

    def test_multi_location_detected(self):
        from odooforge.planning.requirement_parser import analyze_requirements
        result = analyze_requirements("We have 5 store locations across the city")
        assert result["infrastructure"]["multi_company"] is True
        assert result["infrastructure"]["locations"] == 5

    def test_online_needs_detected(self):
        from odooforge.planning.requirement_parser import analyze_requirements
        result = analyze_requirements("We sell online and need a website")
        assert result["infrastructure"]["needs_website"] is True

    def test_delivery_needs_detected(self):
        from odooforge.planning.requirement_parser import analyze_requirements
        result = analyze_requirements("We offer delivery service to customers")
        assert result["infrastructure"]["needs_delivery"] is True

    def test_custom_requirements_detected(self):
        from odooforge.planning.requirement_parser import analyze_requirements
        result = analyze_requirements("I need a customer loyalty tier system with automatic notifications")
        patterns = [r["pattern"] for r in result["custom_requirements"]]
        assert len(patterns) > 0

    def test_questions_generated_for_multi_location(self):
        from odooforge.planning.requirement_parser import analyze_requirements
        result = analyze_requirements("bakery with 3 locations")
        # Should ask about shared vs separate inventory
        assert len(result["questions_for_user"]) > 0

    def test_result_structure(self):
        from odooforge.planning.requirement_parser import analyze_requirements
        result = analyze_requirements("I run a small retail shop")
        assert "industry" in result
        assert "matching_blueprint" in result
        assert "modules_needed" in result
        assert "custom_requirements" in result
        assert "infrastructure" in result
        assert "questions_for_user" in result
        assert isinstance(result["modules_needed"], list)
        assert isinstance(result["questions_for_user"], list)

    def test_blueprint_modules_merged(self):
        from odooforge.planning.requirement_parser import analyze_requirements
        result = analyze_requirements("I run a bakery")
        modules = [m["module"] for m in result["modules_needed"]]
        # Bakery blueprint includes point_of_sale
        assert "point_of_sale" in modules


class TestDesignSolution:
    def _sample_requirements(self) -> dict[str, Any]:
        return {
            "industry": "bakery",
            "matching_blueprint": "bakery",
            "modules_needed": [
                {"module": "point_of_sale", "name": "Point of Sale", "reason": "in-store sales"},
                {"module": "stock", "name": "Inventory", "reason": "inventory tracking"},
            ],
            "custom_requirements": [],
            "infrastructure": {
                "multi_company": False,
                "locations": 0,
                "needs_website": False,
                "needs_delivery": False,
            },
            "questions_for_user": [],
        }

    def test_plan_has_phases(self):
        from odooforge.planning.solution_designer import design_solution
        result = design_solution(self._sample_requirements())
        assert "phases" in result
        assert len(result["phases"]) >= 2  # At least foundation + verification

    def test_foundation_phase_is_first(self):
        from odooforge.planning.solution_designer import design_solution
        result = design_solution(self._sample_requirements())
        assert result["phases"][0]["name"] == "Foundation"
        assert result["phases"][0]["phase"] == 1

    def test_verification_phase_is_last(self):
        from odooforge.planning.solution_designer import design_solution
        result = design_solution(self._sample_requirements())
        assert result["phases"][-1]["name"] == "Verification"

    def test_foundation_has_snapshot(self):
        from odooforge.planning.solution_designer import design_solution
        result = design_solution(self._sample_requirements())
        foundation = result["phases"][0]
        tools = [s["tool"] for s in foundation["steps"]]
        assert "odoo_snapshot_create" in tools

    def test_foundation_has_module_install(self):
        from odooforge.planning.solution_designer import design_solution
        result = design_solution(self._sample_requirements())
        foundation = result["phases"][0]
        tools = [s["tool"] for s in foundation["steps"]]
        assert "odoo_module_install" in tools

    def test_multi_location_adds_phase(self):
        from odooforge.planning.solution_designer import design_solution
        reqs = self._sample_requirements()
        reqs["infrastructure"]["multi_company"] = True
        reqs["infrastructure"]["locations"] = 3
        result = design_solution(reqs)
        phase_names = [p["name"] for p in result["phases"]]
        assert "Multi-Location Setup" in phase_names

    def test_custom_requirements_add_phases(self):
        from odooforge.planning.solution_designer import design_solution
        reqs = self._sample_requirements()
        reqs["custom_requirements"] = [
            {"pattern": "partner_extension", "description": "Customer loyalty", "approach": "configuration"},
        ]
        result = design_solution(reqs)
        assert result["summary"]["total_phases"] >= 3

    def test_plan_summary(self):
        from odooforge.planning.solution_designer import design_solution
        result = design_solution(self._sample_requirements())
        assert "summary" in result
        assert "total_phases" in result["summary"]
        assert "total_steps" in result["summary"]

    def test_integration_phase_for_website(self):
        from odooforge.planning.solution_designer import design_solution
        reqs = self._sample_requirements()
        reqs["infrastructure"]["needs_website"] = True
        result = design_solution(reqs)
        phase_names = [p["name"] for p in result["phases"]]
        assert "Integrations" in phase_names


class TestValidatePlan:
    def _sample_plan(self) -> dict[str, Any]:
        return {
            "plan_id": "test-plan",
            "phases": [
                {
                    "phase": 1,
                    "name": "Foundation",
                    "depends_on": [],
                    "steps": [
                        {"tool": "odoo_snapshot_create", "params": {}, "description": "Snapshot"},
                        {"tool": "odoo_module_install", "params": {"module_names": ["sale", "crm"]}, "description": "Install"},
                    ],
                },
                {
                    "phase": 2,
                    "name": "Custom",
                    "depends_on": [1],
                    "steps": [
                        {"tool": "odoo_schema_field_create", "params": {"model": "res.partner", "field_name": "x_loyalty", "field_type": "char"}, "description": "Add field"},
                    ],
                },
                {
                    "phase": 3,
                    "name": "Verify",
                    "depends_on": [1, 2],
                    "steps": [
                        {"tool": "odoo_diagnostics_health_check", "params": {}, "description": "Health check"},
                    ],
                },
            ],
        }

    def test_valid_plan_passes(self):
        from odooforge.planning.plan_validator import validate_plan
        result = validate_plan(self._sample_plan())
        assert result["valid"] is True

    def test_checks_present(self):
        from odooforge.planning.plan_validator import validate_plan
        result = validate_plan(self._sample_plan())
        check_names = [c["check"] for c in result["checks"]]
        assert "module_compatibility" in check_names
        assert "field_naming" in check_names
        assert "dependency_order" in check_names
        assert "safety_snapshot" in check_names

    def test_field_naming_catches_missing_prefix(self):
        from odooforge.planning.plan_validator import validate_plan
        plan = self._sample_plan()
        plan["phases"][1]["steps"][0]["params"]["field_name"] = "loyalty"  # missing x_
        result = validate_plan(plan)
        field_check = next(c for c in result["checks"] if c["check"] == "field_naming")
        assert field_check["status"] == "fail"

    def test_dependency_catches_circular(self):
        from odooforge.planning.plan_validator import validate_plan
        plan = self._sample_plan()
        plan["phases"][0]["depends_on"] = [2]  # Phase 1 depends on Phase 2 = circular
        result = validate_plan(plan)
        dep_check = next(c for c in result["checks"] if c["check"] == "dependency_order")
        assert dep_check["status"] == "fail"

    def test_missing_snapshot_warns(self):
        from odooforge.planning.plan_validator import validate_plan
        plan = self._sample_plan()
        # Remove snapshot step
        plan["phases"][0]["steps"] = [s for s in plan["phases"][0]["steps"] if s["tool"] != "odoo_snapshot_create"]
        result = validate_plan(plan)
        snap_check = next(c for c in result["checks"] if c["check"] == "safety_snapshot")
        assert snap_check["status"] == "warning"

    def test_unknown_module_warns(self):
        from odooforge.planning.plan_validator import validate_plan
        plan = self._sample_plan()
        plan["phases"][0]["steps"][1]["params"]["module_names"] = ["nonexistent_module_xyz"]
        result = validate_plan(plan)
        mod_check = next(c for c in result["checks"] if c["check"] == "module_compatibility")
        assert mod_check["status"] == "warning"

    def test_summary_counts(self):
        from odooforge.planning.plan_validator import validate_plan
        result = validate_plan(self._sample_plan())
        assert result["summary"]["total_checks"] >= 4
        assert result["summary"]["passed"] >= 3

    def test_empty_plan_validates(self):
        from odooforge.planning.plan_validator import validate_plan
        result = validate_plan({"phases": []})
        assert isinstance(result["valid"], bool)


class TestPlanningToolWrappers:
    """Test the async tool wrappers in tools/planning.py."""

    @pytest.mark.asyncio
    async def test_analyze_requirements_wrapper(self):
        from odooforge.tools.planning import odoo_analyze_requirements
        result = await odoo_analyze_requirements("I run a bakery")
        assert "matching_blueprint" in result

    @pytest.mark.asyncio
    async def test_design_solution_wrapper(self):
        from odooforge.tools.planning import odoo_design_solution
        reqs = {
            "industry": "bakery",
            "matching_blueprint": "bakery",
            "modules_needed": [{"module": "sale", "name": "Sales", "reason": "test"}],
            "custom_requirements": [],
            "infrastructure": {"multi_company": False, "locations": 0, "needs_website": False, "needs_delivery": False},
            "questions_for_user": [],
        }
        result = await odoo_design_solution(reqs)
        assert "phases" in result

    @pytest.mark.asyncio
    async def test_validate_plan_wrapper(self):
        from odooforge.tools.planning import odoo_validate_plan
        plan = {"phases": [{"phase": 1, "name": "Test", "depends_on": [], "steps": []}]}
        result = await odoo_validate_plan(plan)
        assert "valid" in result
