"""Tests for MCP server initialization and tool registration."""

import pytest
from unittest.mock import patch, MagicMock


class TestServerInit:
    def test_server_name(self):
        from odooforge.server import mcp
        assert mcp.name == "OdooForge"

    def test_tool_count(self):
        from odooforge.server import mcp
        tools = mcp._tool_manager._tools
        assert len(tools) == 74, f"Expected 74 tools, got {len(tools)}: {list(tools.keys())}"

    def test_expected_tools_registered(self):
        from odooforge.server import mcp
        tools = set(mcp._tool_manager._tools.keys())

        expected = {
            # Phase 1
            "odoo_instance_start", "odoo_instance_stop", "odoo_instance_restart",
            "odoo_instance_status", "odoo_instance_logs",
            "odoo_db_create", "odoo_db_list", "odoo_db_backup",
            "odoo_db_restore", "odoo_db_drop", "odoo_db_run_sql",
            "odoo_record_search", "odoo_record_read", "odoo_record_create",
            "odoo_record_update", "odoo_record_delete", "odoo_record_execute",
            # Phase 2
            "odoo_snapshot_create", "odoo_snapshot_list",
            "odoo_snapshot_restore", "odoo_snapshot_delete",
            "odoo_module_list_available", "odoo_module_list_installed",
            "odoo_module_info", "odoo_module_install",
            "odoo_module_upgrade", "odoo_module_uninstall",
            "odoo_model_list", "odoo_model_fields", "odoo_model_search_field",
            "odoo_schema_field_create", "odoo_schema_field_update",
            "odoo_schema_field_delete", "odoo_schema_model_create",
            "odoo_schema_list_custom",
            # Phase 3
            "odoo_view_list", "odoo_view_get_arch", "odoo_view_modify",
            "odoo_view_reset", "odoo_view_list_customizations",
            "odoo_report_list", "odoo_report_get_template",
            "odoo_report_modify", "odoo_report_preview",
            "odoo_report_reset", "odoo_report_layout_configure",
            "odoo_automation_list", "odoo_automation_create",
            "odoo_automation_update", "odoo_automation_delete",
            "odoo_email_template_create",
            "odoo_network_expose", "odoo_network_status", "odoo_network_stop",
            # Phase 4
            "odoo_import_preview", "odoo_import_execute", "odoo_import_template",
            "odoo_email_configure_outgoing", "odoo_email_configure_incoming",
            "odoo_email_test", "odoo_email_dns_guide",
            "odoo_settings_get", "odoo_settings_set",
            "odoo_company_configure", "odoo_users_manage",
            "odoo_knowledge_module_info", "odoo_knowledge_search",
            "odoo_knowledge_community_gaps",
            "odoo_diagnostics_health_check",
            # Planning
            "odoo_analyze_requirements", "odoo_design_solution", "odoo_validate_plan",
            # Phase 5
            "odoo_recipe_list", "odoo_recipe_execute",
        }
        assert expected.issubset(tools), f"Missing tools: {expected - tools}"

    def test_main_entry_point_exists(self):
        from odooforge.server import main
        assert callable(main)


class TestServerResources:
    def test_modules_resource_registered(self):
        from odooforge.server import mcp
        resources = mcp._resource_manager._resources
        assert any("modules" in str(uri) for uri in resources), \
            f"modules resource not found in {list(resources.keys())}"

    def test_dictionary_resource_registered(self):
        from odooforge.server import mcp
        resources = mcp._resource_manager._resources
        assert any("dictionary" in str(uri) for uri in resources), \
            f"dictionary resource not found in {list(resources.keys())}"

    def test_patterns_resource_registered(self):
        from odooforge.server import mcp
        resources = mcp._resource_manager._resources
        assert any("patterns" in str(uri) for uri in resources), \
            f"patterns resource not found in {list(resources.keys())}"

    def test_best_practices_resource_registered(self):
        from odooforge.server import mcp
        resources = mcp._resource_manager._resources
        assert any("best-practices" in str(uri) for uri in resources), \
            f"best-practices resource not found in {list(resources.keys())}"

    def test_blueprints_index_resource_registered(self):
        from odooforge.server import mcp
        resources = mcp._resource_manager._resources
        assert any("blueprints" in str(uri) for uri in resources), \
            f"blueprints resource not found in {list(resources.keys())}"

    def test_blueprint_template_resource_registered(self):
        from odooforge.server import mcp
        templates = mcp._resource_manager._templates
        assert any("{industry}" in str(t) for t in templates), \
            f"Blueprint template resource not found in {list(templates.keys())}"

    def test_resource_count_minimum(self):
        from odooforge.server import mcp
        resources = mcp._resource_manager._resources
        templates = mcp._resource_manager._templates
        total = len(resources) + len(templates)
        assert total >= 6, f"Expected at least 6 resources, got {total}"

    def test_knowledge_modules_returns_valid_json(self):
        import json
        from odooforge.server import knowledge_modules
        result = knowledge_modules()
        data = json.loads(result)
        assert isinstance(data, dict)
        assert "sale" in data

    def test_knowledge_dictionary_returns_valid_json(self):
        import json
        from odooforge.server import knowledge_dictionary
        result = knowledge_dictionary()
        data = json.loads(result)
        assert isinstance(data, dict)
        assert "customer" in data

    def test_knowledge_blueprint_returns_valid_json(self):
        import json
        from odooforge.server import knowledge_blueprint
        result = knowledge_blueprint("bakery")
        data = json.loads(result)
        assert isinstance(data, dict)
        assert "modules" in data

    def test_knowledge_blueprint_unknown_returns_error(self):
        import json
        from odooforge.server import knowledge_blueprint
        result = knowledge_blueprint("nonexistent")
        data = json.loads(result)
        assert "error" in data
        assert "available" in data


class TestServerPrompts:
    def test_prompt_count(self):
        from odooforge.server import mcp
        prompts = mcp._prompt_manager._prompts
        assert len(prompts) >= 4, f"Expected at least 4 prompts, got {len(prompts)}"

    def test_business_setup_prompt_registered(self):
        from odooforge.server import mcp
        prompts = mcp._prompt_manager._prompts
        assert "business-setup" in prompts

    def test_feature_builder_prompt_registered(self):
        from odooforge.server import mcp
        prompts = mcp._prompt_manager._prompts
        assert "feature-builder" in prompts

    def test_module_generator_prompt_registered(self):
        from odooforge.server import mcp
        prompts = mcp._prompt_manager._prompts
        assert "module-generator" in prompts

    def test_troubleshooter_prompt_registered(self):
        from odooforge.server import mcp
        prompts = mcp._prompt_manager._prompts
        assert "troubleshooter" in prompts

    def test_business_setup_prompt_returns_content(self):
        from odooforge.server import prompt_business_setup
        result = prompt_business_setup()
        assert isinstance(result, str)
        assert len(result) > 100
        assert "business" in result.lower()
        assert "snapshot" in result.lower()

    def test_feature_builder_prompt_returns_content(self):
        from odooforge.server import prompt_feature_builder
        result = prompt_feature_builder()
        assert isinstance(result, str)
        assert len(result) > 100
        assert "x_" in result  # mentions x_ prefix convention

    def test_module_generator_prompt_returns_content(self):
        from odooforge.server import prompt_module_generator
        result = prompt_module_generator()
        assert isinstance(result, str)
        assert len(result) > 100
        assert "manifest" in result.lower() or "security" in result.lower()

    def test_troubleshooter_prompt_returns_content(self):
        from odooforge.server import prompt_troubleshooter
        result = prompt_troubleshooter()
        assert isinstance(result, str)
        assert len(result) > 100
        assert "snapshot" in result.lower()

    def test_prompts_reference_knowledge_resources(self):
        """Non-diagnostic workflow prompts should reference knowledge resources."""
        from odooforge.server import (
            prompt_business_setup, prompt_feature_builder,
            prompt_module_generator,
        )
        for prompt_fn in [prompt_business_setup, prompt_feature_builder, prompt_module_generator]:
            content = prompt_fn()
            assert "odoo://knowledge/" in content, \
                f"{prompt_fn.__name__} should reference knowledge resources"
