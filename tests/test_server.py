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
        assert len(tools) == 71, f"Expected 71 tools, got {len(tools)}: {list(tools.keys())}"

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
            # Phase 5
            "odoo_recipe_list", "odoo_recipe_execute",
        }
        assert expected.issubset(tools), f"Missing tools: {expected - tools}"

    def test_main_entry_point_exists(self):
        from odooforge.server import main
        assert callable(main)
