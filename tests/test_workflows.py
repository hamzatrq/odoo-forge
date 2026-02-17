"""Tests for workflow orchestration planners."""

from __future__ import annotations

import pytest

from odooforge.workflows.setup_business import setup_business
from odooforge.workflows.create_feature import create_feature
from odooforge.workflows.create_dashboard import create_dashboard
from odooforge.workflows.setup_integration import setup_integration


# ── Setup Business ────────────────────────────────────────────────


class TestSetupBusiness:
    def test_valid_blueprint_returns_steps(self):
        result = setup_business("bakery", "My Bakery", "testdb")
        assert result["workflow"] == "setup_business"
        assert result["blueprint"] == "bakery"
        assert isinstance(result["steps"], list)
        assert len(result["steps"]) > 0

    def test_unknown_blueprint_returns_error(self):
        result = setup_business("nonexistent", "Foo", "testdb")
        assert result["status"] == "error"
        assert "nonexistent" in result["message"]
        assert isinstance(result["available"], list)
        assert "bakery" in result["available"]

    def test_dry_run_flag_preserved(self):
        result_dry = setup_business("bakery", "B", "db", dry_run=True)
        result_live = setup_business("bakery", "B", "db", dry_run=False)
        assert result_dry["dry_run"] is True
        assert result_live["dry_run"] is False

    def test_snapshot_is_first_step(self):
        result = setup_business("bakery", "B", "db")
        first = result["steps"][0]
        assert first["step"] == 1
        assert first["tool"] == "odoo_snapshot_create"

    def test_health_check_is_last_step(self):
        result = setup_business("bakery", "B", "db")
        last = result["steps"][-1]
        assert last["tool"] == "odoo_diagnostics_health_check"

    def test_multi_location_adds_company_create_steps(self):
        result_single = setup_business("bakery", "B", "db", locations=1)
        result_multi = setup_business("bakery", "B", "db", locations=3)
        # Multi-location should have more steps (enable multi-company + 2 branch creates)
        single_tools = [s["tool"] for s in result_single["steps"]]
        multi_tools = [s["tool"] for s in result_multi["steps"]]
        assert single_tools.count("odoo_record_create") == 0
        assert multi_tools.count("odoo_record_create") == 2  # locations 2 and 3
        assert "odoo_settings_set" in multi_tools  # enable multi-company

    def test_step_count_matches_summary(self):
        result = setup_business("bakery", "B", "db")
        assert result["summary"]["total_steps"] == len(result["steps"])

    def test_modules_count_in_summary(self):
        result = setup_business("bakery", "B", "db")
        # bakery blueprint has modules; summary should reflect count
        assert result["summary"]["modules_to_install"] > 0

    def test_automations_in_summary(self):
        result = setup_business("bakery", "B", "db")
        auto_steps = [s for s in result["steps"] if s["tool"] == "odoo_automation_create"]
        assert result["summary"]["automations"] == len(auto_steps)

    def test_custom_fields_in_summary(self):
        result = setup_business("bakery", "B", "db")
        field_steps = [s for s in result["steps"] if s["tool"] == "odoo_schema_field_create"]
        assert result["summary"]["custom_fields"] == len(field_steps)

    def test_steps_have_sequential_numbers(self):
        result = setup_business("bakery", "B", "db", locations=2)
        for i, step in enumerate(result["steps"]):
            assert step["step"] == i + 1

    def test_each_step_has_required_keys(self):
        result = setup_business("bakery", "B", "db")
        for step in result["steps"]:
            assert "step" in step
            assert "tool" in step
            assert "params" in step
            assert "description" in step


# ── Create Feature ────────────────────────────────────────────────


class TestCreateFeature:
    FIELDS = [
        {"name": "x_priority", "type": "Selection", "label": "Priority"},
        {"name": "x_due_date", "type": "Date", "label": "Due Date"},
    ]

    def test_generates_field_creation_steps(self):
        result = create_feature("Task Tracking", "project.task", self.FIELDS, "db")
        field_steps = [s for s in result["steps"] if s["tool"] == "odoo_schema_field_create"]
        assert len(field_steps) == 2

    def test_includes_view_modification_steps(self):
        result = create_feature("Task Tracking", "project.task", self.FIELDS, "db")
        view_steps = [s for s in result["steps"] if s["tool"] == "odoo_view_modify"]
        assert len(view_steps) == 2  # form + tree

    def test_no_view_steps_when_disabled(self):
        result = create_feature(
            "Task Tracking", "project.task", self.FIELDS, "db", add_to_views=False,
        )
        view_steps = [s for s in result["steps"] if s["tool"] == "odoo_view_modify"]
        assert len(view_steps) == 0

    def test_automation_step_when_provided(self):
        auto = {"name": "Auto-assign priority", "trigger": "on_create"}
        result = create_feature(
            "Task Tracking", "project.task", self.FIELDS, "db", automation=auto,
        )
        auto_steps = [s for s in result["steps"] if s["tool"] == "odoo_automation_create"]
        assert len(auto_steps) == 1
        assert auto_steps[0]["params"]["name"] == "Auto-assign priority"

    def test_no_automation_step_when_none(self):
        result = create_feature("Task Tracking", "project.task", self.FIELDS, "db")
        auto_steps = [s for s in result["steps"] if s["tool"] == "odoo_automation_create"]
        assert len(auto_steps) == 0

    def test_snapshot_first(self):
        result = create_feature("Test", "res.partner", self.FIELDS, "db")
        assert result["steps"][0]["tool"] == "odoo_snapshot_create"

    def test_verify_step_at_end(self):
        result = create_feature("Test", "res.partner", self.FIELDS, "db")
        assert result["steps"][-1]["tool"] == "odoo_model_fields"

    def test_summary_counts(self):
        result = create_feature("Test", "res.partner", self.FIELDS, "db")
        assert result["summary"]["fields_to_create"] == 2
        assert result["summary"]["views_modified"] == 2
        assert result["summary"]["automation"] is False

    def test_dry_run_flag(self):
        result = create_feature("Test", "res.partner", self.FIELDS, "db", dry_run=False)
        assert result["dry_run"] is False

    def test_steps_have_sequential_numbers(self):
        result = create_feature("Test", "res.partner", self.FIELDS, "db")
        for i, step in enumerate(result["steps"]):
            assert step["step"] == i + 1


# ── Create Dashboard ─────────────────────────────────────────────


class TestCreateDashboard:
    METRICS = [
        {"model": "sale.order", "measure": "amount_total", "label": "Total Sales"},
        {"model": "purchase.order", "measure": "amount_total", "label": "Total Purchases"},
    ]

    def test_generates_action_creation_steps(self):
        result = create_dashboard("Sales Dashboard", self.METRICS, "db")
        action_steps = [
            s for s in result["steps"]
            if s["tool"] == "odoo_record_create"
            and s["params"].get("model") == "ir.actions.act_window"
        ]
        assert len(action_steps) == 2

    def test_generates_menu_step(self):
        result = create_dashboard("Sales Dashboard", self.METRICS, "db")
        menu_steps = [
            s for s in result["steps"]
            if s["tool"] == "odoo_record_create"
            and s["params"].get("model") == "ir.ui.menu"
        ]
        # 1 parent + 2 children
        assert len(menu_steps) == 3

    def test_snapshot_first(self):
        result = create_dashboard("Sales Dashboard", self.METRICS, "db")
        assert result["steps"][0]["tool"] == "odoo_snapshot_create"

    def test_health_check_last(self):
        result = create_dashboard("Sales Dashboard", self.METRICS, "db")
        assert result["steps"][-1]["tool"] == "odoo_diagnostics_health_check"

    def test_summary_counts(self):
        result = create_dashboard("Sales Dashboard", self.METRICS, "db")
        assert result["summary"]["metrics_count"] == 2
        assert result["summary"]["actions_created"] == 2
        assert result["summary"]["menu_items_created"] == 3

    def test_dry_run_flag(self):
        result = create_dashboard("Sales Dashboard", self.METRICS, "db", dry_run=False)
        assert result["dry_run"] is False

    def test_total_steps_in_summary(self):
        result = create_dashboard("Sales Dashboard", self.METRICS, "db")
        assert result["summary"]["total_steps"] == len(result["steps"])


# ── Setup Integration ────────────────────────────────────────────


class TestSetupIntegration:
    def test_email_generates_mail_config_steps(self):
        result = setup_integration("email", "gmail", "db", {"smtp_user": "a@b.com"})
        tools = [s["tool"] for s in result["steps"]]
        assert "odoo_email_configure_outgoing" in tools
        assert "odoo_email_configure_incoming" in tools
        assert "odoo_email_test" in tools

    def test_payment_generates_payment_steps(self):
        result = setup_integration("payment", "stripe", "db", {"state": "test"})
        tools = [s["tool"] for s in result["steps"]]
        assert "odoo_module_install" in tools
        # Check that stripe module is installed
        install_step = next(s for s in result["steps"] if s["tool"] == "odoo_module_install")
        assert "payment_stripe" in install_step["params"]["module_names"]

    def test_shipping_generates_delivery_steps(self):
        result = setup_integration("shipping", "fedex", "db", {})
        tools = [s["tool"] for s in result["steps"]]
        assert "odoo_module_install" in tools
        install_step = next(s for s in result["steps"] if s["tool"] == "odoo_module_install")
        assert "delivery_fedex" in install_step["params"]["module_names"]
        assert "delivery" in install_step["params"]["module_names"]

    def test_unknown_type_returns_error(self):
        result = setup_integration("fax", "hp", "db", {})
        assert result["status"] == "error"
        assert "fax" in result["message"]
        assert isinstance(result["supported_types"], list)

    def test_snapshot_first(self):
        result = setup_integration("email", "gmail", "db", {})
        assert result["steps"][0]["tool"] == "odoo_snapshot_create"

    def test_health_check_last(self):
        result = setup_integration("email", "gmail", "db", {})
        assert result["steps"][-1]["tool"] == "odoo_diagnostics_health_check"

    def test_dry_run_flag(self):
        result = setup_integration("email", "gmail", "db", {}, dry_run=False)
        assert result["dry_run"] is False

    def test_steps_have_sequential_numbers(self):
        result = setup_integration("email", "gmail", "db", {})
        for i, step in enumerate(result["steps"]):
            assert step["step"] == i + 1

    def test_total_steps_in_summary(self):
        result = setup_integration("payment", "stripe", "db", {})
        assert result["summary"]["total_steps"] == len(result["steps"])
