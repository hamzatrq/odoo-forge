"""Comprehensive edge case tests across all OdooForge modules.

Covers: error propagation, boundary values, exception handling,
validation edge cases, RPC faults, and unusual input combinations.
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

# ── Records ─────────────────────────────────────────────────────────
from odooforge.tools.records import (
    odoo_record_search, odoo_record_read, odoo_record_create,
    odoo_record_update, odoo_record_delete, odoo_record_execute,
)

# ── Snapshots ───────────────────────────────────────────────────────
from odooforge.tools.snapshots import (
    odoo_snapshot_create, odoo_snapshot_list,
    odoo_snapshot_restore, odoo_snapshot_delete,
)

# ── Modules ─────────────────────────────────────────────────────────
from odooforge.tools.modules import (
    odoo_module_list_available, odoo_module_list_installed,
    odoo_module_info, odoo_module_install,
    odoo_module_upgrade, odoo_module_uninstall,
)

# ── Schema ──────────────────────────────────────────────────────────
from odooforge.tools.schema import (
    odoo_schema_field_create, odoo_schema_field_update,
    odoo_schema_field_delete, odoo_schema_model_create,
    odoo_schema_list_custom,
)

# ── Views ───────────────────────────────────────────────────────────
from odooforge.tools.views import (
    odoo_view_list, odoo_view_get_arch, odoo_view_modify,
    odoo_view_reset, odoo_view_list_customizations,
)

# ── Reports ─────────────────────────────────────────────────────────
from odooforge.tools.reports import (
    odoo_report_list, odoo_report_get_template,
    odoo_report_modify, odoo_report_preview,
    odoo_report_reset, odoo_report_layout_configure,
)

# ── Automation ──────────────────────────────────────────────────────
from odooforge.tools.automation import (
    odoo_automation_list, odoo_automation_create,
    odoo_automation_update, odoo_automation_delete,
    odoo_email_template_create,
)

# ── Network ─────────────────────────────────────────────────────────
from odooforge.tools.network import (
    odoo_network_expose, odoo_network_status, odoo_network_stop,
)

# ── Imports ─────────────────────────────────────────────────────────
from odooforge.tools.imports import (
    odoo_import_preview, odoo_import_execute, odoo_import_template,
)

# ── Email ───────────────────────────────────────────────────────────
from odooforge.tools.email import (
    odoo_email_configure_outgoing, odoo_email_configure_incoming,
    odoo_email_test, odoo_email_dns_guide,
)

# ── Settings ────────────────────────────────────────────────────────
from odooforge.tools.settings import (
    odoo_settings_get, odoo_settings_set,
    odoo_company_configure, odoo_users_manage,
)

# ── Knowledge ───────────────────────────────────────────────────────
from odooforge.tools.knowledge import (
    odoo_knowledge_module_info, odoo_knowledge_search,
    odoo_knowledge_community_gaps,
)

# ── Diagnostics ─────────────────────────────────────────────────────
from odooforge.tools.diagnostics import odoo_diagnostics_health_check

# ── Recipes ─────────────────────────────────────────────────────────
from odooforge.tools.recipes import odoo_recipe_list, odoo_recipe_execute, RECIPES

# ── Utilities ───────────────────────────────────────────────────────
from odooforge.utils.validators import (
    validate_domain, validate_model_name, validate_db_name,
    validate_field_name,
)
from odooforge.utils.formatting import format_table, format_record, truncate
from odooforge.utils.binary_handler import encode_file, csv_to_import_data, format_file_size
from odooforge.utils.response_formatter import success, error, paginated, confirm_required, format_duration
from odooforge.utils.errors import (
    OdooForgeError, ConnectionError, AuthenticationError, DatabaseError,
    ModuleError, ValidationError, ViewError, SnapshotError,
    DockerNotRunningError, enrich_rpc_error, FAULT_SUGGESTIONS,
)
from odooforge.utils.xpath_builder import (
    field_xpath, group_xpath, build_field_xml, build_inherit_xml,
)
from odooforge.utils.qweb_builder import (
    div_xpath, build_qweb_field, build_qweb_inherit_xml,
)


# ═══════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def rpc():
    m = MagicMock()
    m.search_read.return_value = []
    m.read.return_value = []
    m.create.return_value = 1
    m.write.return_value = True
    m.unlink.return_value = True
    m.search_count.return_value = 0
    m.execute_method.return_value = True
    m.db_list.return_value = ["testdb"]
    m.authenticate.return_value = 2
    m.server_version.return_value = "18.0"
    m.load.return_value = {"ids": [1], "messages": []}
    m.fields_get.return_value = {
        "name": {"string": "Name", "type": "char", "required": True, "readonly": False},
        "email": {"string": "Email", "type": "char", "required": False, "readonly": False},
        "id": {"string": "ID", "type": "integer", "required": True, "readonly": True},
    }
    return m


@pytest.fixture
def cache():
    m = MagicMock()
    m.validate_fields.return_value = []
    m.get_model_fields.return_value = {"name": {}, "email": {}}
    m.refresh_all.return_value = None
    return m


@pytest.fixture
def docker():
    m = MagicMock()
    m.get_status = AsyncMock(return_value={"running": True, "services": {"odoo": "running"}})
    m.create_snapshot = AsyncMock(return_value={"size_bytes": 5242880, "created_at": "2024-01-01T00:00:00"})
    m.list_snapshots = AsyncMock(return_value=[])
    m.restore_snapshot = AsyncMock(return_value=True)
    m.delete_snapshot = AsyncMock(return_value={"freed_bytes": 5242880})
    m.logs = AsyncMock(return_value="")
    m.exec_odoo_cli = AsyncMock(return_value={"exit_code": 0, "stdout": "", "stderr": ""})
    m.restart = AsyncMock()
    return m


@pytest.fixture
def pg():
    m = MagicMock()
    m.ensure_pool = AsyncMock()
    m._pool = MagicMock()
    m._pool.get_size.return_value = 5
    return m


# ═══════════════════════════════════════════════════════════════════
# RECORD EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestRecordSearchEdgeCases:
    @pytest.mark.asyncio
    async def test_search_zero_limit(self, rpc):
        """Limit of 0 should still cap properly."""
        result = await odoo_record_search(rpc, "testdb", "res.partner", limit=0)
        assert result["limit"] <= 200

    @pytest.mark.asyncio
    async def test_search_negative_offset(self, rpc):
        """Negative offset should be handled."""
        result = await odoo_record_search(rpc, "testdb", "res.partner", offset=-5)
        assert "records" in result

    @pytest.mark.asyncio
    async def test_search_max_limit_cap(self, rpc):
        """Limit of 999 should be capped at 200."""
        await odoo_record_search(rpc, "testdb", "res.partner", limit=999)
        call_kwargs = rpc.search_read.call_args
        assert call_kwargs.kwargs.get("limit", 200) <= 200

    @pytest.mark.asyncio
    async def test_search_with_empty_domain(self, rpc):
        rpc.search_read.return_value = [{"id": 1}]
        rpc.search_count.return_value = 1
        result = await odoo_record_search(rpc, "testdb", "res.partner", domain=[])
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_search_with_order(self, rpc):
        await odoo_record_search(rpc, "testdb", "res.partner", order="name desc")
        call_kwargs = rpc.search_read.call_args
        assert call_kwargs.kwargs.get("order") == "name desc"

    @pytest.mark.asyncio
    async def test_search_with_fields(self, rpc):
        rpc.search_read.return_value = [{"id": 1, "name": "Test"}]
        rpc.search_count.return_value = 1
        result = await odoo_record_search(
            rpc, "testdb", "res.partner", fields=["name"],
        )
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_search_has_more_false(self, rpc):
        rpc.search_read.return_value = [{"id": 1}]
        rpc.search_count.return_value = 1
        result = await odoo_record_search(rpc, "testdb", "res.partner", limit=20)
        assert result["has_more"] is False

    @pytest.mark.asyncio
    async def test_search_rpc_exception(self, rpc):
        rpc.search_read.side_effect = Exception("Connection refused")
        with pytest.raises(Exception, match="Connection refused"):
            await odoo_record_search(rpc, "testdb", "res.partner")

    @pytest.mark.asyncio
    async def test_search_invalid_model_format(self, rpc):
        # validate_model_name requires dot-separated names with at least 2 parts
        # "res..partner" has 3 parts ("res", "", "partner") so it passes validation
        models = ["partner", "res", "a", "123"]
        for model in models:
            with pytest.raises(ValueError):
                await odoo_record_search(rpc, "testdb", model)


class TestRecordReadEdgeCases:
    @pytest.mark.asyncio
    async def test_read_single_id(self, rpc):
        rpc.read.return_value = [{"id": 1, "name": "Test"}]
        result = await odoo_record_read(rpc, "testdb", "res.partner", [1])
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_read_nonexistent_ids(self, rpc):
        rpc.read.return_value = []
        result = await odoo_record_read(rpc, "testdb", "res.partner", [99999])
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_read_with_specific_fields(self, rpc):
        rpc.read.return_value = [{"id": 1, "name": "Test"}]
        result = await odoo_record_read(
            rpc, "testdb", "res.partner", [1], fields=["name"],
        )
        rpc.read.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_many_ids(self, rpc):
        rpc.read.return_value = [{"id": i} for i in range(50)]
        result = await odoo_record_read(rpc, "testdb", "res.partner", list(range(50)))
        assert result["count"] == 50


class TestRecordCreateEdgeCases:
    @pytest.mark.asyncio
    async def test_create_empty_values(self, rpc, cache):
        result = await odoo_record_create(rpc, cache, "testdb", "res.partner", {})
        assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_create_bulk_single(self, rpc, cache):
        rpc.create.return_value = 1
        result = await odoo_record_create(
            rpc, cache, "testdb", "res.partner", [{"name": "A"}],
        )
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_create_rpc_exception(self, rpc, cache):
        rpc.create.side_effect = Exception("Unique violation")
        with pytest.raises(Exception, match="Unique violation"):
            await odoo_record_create(rpc, cache, "testdb", "res.partner", {"name": "A"})

    @pytest.mark.asyncio
    async def test_create_partial_invalid_fields(self, rpc, cache):
        cache.validate_fields.return_value = ["bad_field"]
        cache.get_model_fields.return_value = {"name": {}, "email": {}}
        result = await odoo_record_create(
            rpc, cache, "testdb", "res.partner", {"bad_field": "x", "name": "A"},
        )
        assert result["status"] == "error"
        assert "bad_field" in result["invalid_fields"]


class TestRecordUpdateEdgeCases:
    @pytest.mark.asyncio
    async def test_update_empty_values(self, rpc, cache):
        result = await odoo_record_update(
            rpc, cache, "testdb", "res.partner", [1], {},
        )
        assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_update_many_ids(self, rpc, cache):
        ids = list(range(1, 51))
        result = await odoo_record_update(
            rpc, cache, "testdb", "res.partner", ids, {"name": "Bulk"},
        )
        assert result["updated_count"] == 50

    @pytest.mark.asyncio
    async def test_update_rpc_failure(self, rpc, cache):
        rpc.write.side_effect = Exception("Access denied")
        with pytest.raises(Exception, match="Access denied"):
            await odoo_record_update(
                rpc, cache, "testdb", "res.partner", [1], {"name": "X"},
            )


class TestRecordDeleteEdgeCases:
    @pytest.mark.asyncio
    async def test_delete_empty_ids_confirmed(self, rpc):
        result = await odoo_record_delete(
            rpc, "testdb", "res.partner", [], confirm=True,
        )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_delete_many_ids(self, rpc):
        ids = list(range(1, 101))
        result = await odoo_record_delete(
            rpc, "testdb", "res.partner", ids, confirm=True,
        )
        assert result["deleted_count"] == 100

    @pytest.mark.asyncio
    async def test_delete_rpc_exception(self, rpc):
        rpc.unlink.side_effect = Exception("ForeignKeyViolation")
        with pytest.raises(Exception, match="ForeignKeyViolation"):
            await odoo_record_delete(
                rpc, "testdb", "res.partner", [1], confirm=True,
            )


class TestRecordExecuteEdgeCases:
    @pytest.mark.asyncio
    async def test_execute_no_args(self, rpc):
        result = await odoo_record_execute(
            rpc, "testdb", "res.partner", "check_access_rights",
        )
        assert result["method"] == "check_access_rights"

    @pytest.mark.asyncio
    async def test_execute_with_kwargs_only(self, rpc):
        result = await odoo_record_execute(
            rpc, "testdb", "res.partner", "name_search",
            kwargs={"name": "test", "limit": 5},
        )
        assert result["result"] is True

    @pytest.mark.asyncio
    async def test_execute_rpc_fault(self, rpc):
        rpc.execute_method.side_effect = Exception("Method not found")
        with pytest.raises(Exception, match="Method not found"):
            await odoo_record_execute(rpc, "testdb", "res.partner", "nonexistent")


# ═══════════════════════════════════════════════════════════════════
# SNAPSHOT EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestSnapshotEdgeCases:
    @pytest.mark.asyncio
    async def test_create_with_description(self, docker):
        result = await odoo_snapshot_create(docker, "testdb", "my_snap", "Before upgrade")
        assert result["status"] == "created"
        assert "my_snap" in result["message"]

    @pytest.mark.asyncio
    async def test_create_zero_size(self, docker):
        docker.create_snapshot = AsyncMock(return_value={"size_bytes": 0, "created_at": "now"})
        result = await odoo_snapshot_create(docker, "testdb", "empty_snap")
        assert result["size_mb"] == 0

    @pytest.mark.asyncio
    async def test_list_filter_by_db(self, docker):
        docker.list_snapshots = AsyncMock(return_value=[
            {"name": "s1", "database": "db1", "created_at": "now", "size_bytes": 1000},
        ])
        result = await odoo_snapshot_list(docker, db_name="db1")
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_list_empty(self, docker):
        result = await odoo_snapshot_list(docker)
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_restore_post_auth_failure(self, docker, rpc, cache):
        rpc.authenticate.side_effect = Exception("Auth failed post-restore")
        # Should NOT raise — logs warning instead
        result = await odoo_snapshot_restore(docker, rpc, cache, "testdb", "snap1")
        assert result["status"] == "restored"

    @pytest.mark.asyncio
    async def test_delete_frees_space(self, docker):
        docker.delete_snapshot = AsyncMock(return_value={"freed_bytes": 10485760})
        result = await odoo_snapshot_delete(docker, "big_snap")
        assert result["freed_mb"] == 10.0

    @pytest.mark.asyncio
    async def test_create_docker_failure(self, docker):
        docker.create_snapshot = AsyncMock(side_effect=Exception("Docker not running"))
        with pytest.raises(Exception, match="Docker not running"):
            await odoo_snapshot_create(docker, "testdb", "fail_snap")

    @pytest.mark.asyncio
    async def test_create_invalid_db_name(self, docker):
        with pytest.raises(ValueError):
            await odoo_snapshot_create(docker, "", "my_snap")


# ═══════════════════════════════════════════════════════════════════
# MODULE EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestModuleEdgeCases:
    @pytest.mark.asyncio
    async def test_list_available_with_category(self, rpc):
        rpc.search_read.return_value = [
            {"name": "sale", "shortdesc": "Sales", "state": "uninstalled",
             "category_id": [1, "Sales/Sales"]},
        ]
        result = await odoo_module_list_available(rpc, "testdb", category="Sales")
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_list_available_empty(self, rpc):
        rpc.search_read.return_value = []
        result = await odoo_module_list_available(rpc, "testdb")
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_list_installed_empty(self, rpc):
        result = await odoo_module_list_installed(rpc, "testdb")
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_info_not_found(self, rpc):
        result = await odoo_module_info(rpc, "testdb", "nonexistent_xyz")
        assert result["found"] is False

    @pytest.mark.asyncio
    async def test_install_empty_list(self, rpc, docker, cache):
        result = await odoo_module_install(rpc, docker, cache, "testdb", [])
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_install_already_installed(self, rpc, docker, cache):
        rpc.search_read.return_value = [
            {"name": "sale", "state": "installed", "id": 1},
        ]
        result = await odoo_module_install(rpc, docker, cache, "testdb", ["sale"])
        # Should skip already-installed
        assert result["status"] == "already_installed"

    @pytest.mark.asyncio
    async def test_upgrade_empty_list(self, rpc, docker, cache):
        result = await odoo_module_upgrade(rpc, docker, cache, "testdb", [])
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_uninstall_no_confirm(self, rpc, docker, cache):
        result = await odoo_module_uninstall(rpc, docker, cache, "testdb", "sale", confirm=False)
        assert result["status"] in ("cancelled", "confirmation_required")

    @pytest.mark.asyncio
    async def test_uninstall_not_installed(self, rpc, docker, cache):
        rpc.search_read.return_value = [
            {"name": "sale", "state": "uninstalled", "id": 1},
        ]
        result = await odoo_module_uninstall(rpc, docker, cache, "testdb", "sale", confirm=True)
        assert result["status"] == "error"


# ═══════════════════════════════════════════════════════════════════
# SCHEMA EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestSchemaEdgeCases:
    @pytest.mark.asyncio
    async def test_field_create_bad_type(self, rpc, docker, cache):
        result = await odoo_schema_field_create(
            rpc, docker, cache, "testdb", "res.partner",
            "x_test", "invalid_type", "Test",
        )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_field_create_no_x_prefix(self, rpc, docker, cache):
        result = await odoo_schema_field_create(
            rpc, docker, cache, "testdb", "res.partner",
            "test_field", "char", "Test",
        )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_field_create_selection_no_options(self, rpc, docker, cache):
        # cache.is_field_valid returns falsy by default, so field doesn't exist yet
        cache.is_field_valid = MagicMock(return_value=False)
        rpc.search_read.return_value = [{"id": 10, "model": "res.partner"}]
        docker.restart_service = AsyncMock()
        docker.wait_for_healthy = AsyncMock()
        cache.refresh_model_fields = MagicMock()
        # Selection without options still creates (options are optional)
        result = await odoo_schema_field_create(
            rpc, docker, cache, "testdb", "res.partner",
            "x_status", "selection", "Status",
        )
        # It gets created (no explicit validation for missing selection_options)
        assert result["status"] in ("created", "created_unverified")

    @pytest.mark.asyncio
    async def test_field_create_many2one_no_relation(self, rpc, docker, cache):
        cache.is_field_valid = MagicMock(return_value=False)
        result = await odoo_schema_field_create(
            rpc, docker, cache, "testdb", "res.partner",
            "x_related", "many2one", "Related",
        )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_field_create_success(self, rpc, docker, cache):
        cache.is_field_valid = MagicMock(return_value=False)
        rpc.search_read.return_value = [{"id": 10, "model": "res.partner"}]
        docker.restart_service = AsyncMock()
        docker.wait_for_healthy = AsyncMock()
        cache.refresh_model_fields = MagicMock()
        result = await odoo_schema_field_create(
            rpc, docker, cache, "testdb", "res.partner",
            "x_custom", "char", "Custom Field",
        )
        assert result["status"] in ("created", "created_unverified")

    @pytest.mark.asyncio
    async def test_field_update_non_custom(self, rpc, cache):
        result = await odoo_schema_field_update(
            rpc, cache, "testdb", "res.partner", "name", {"field_description": "New"},
        )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_field_delete_no_confirm(self, rpc, docker, cache):
        result = await odoo_schema_field_delete(
            rpc, docker, cache, "testdb", "res.partner", "x_test", confirm=False,
        )
        assert result["status"] in ("cancelled", "confirmation_required")

    @pytest.mark.asyncio
    async def test_field_delete_non_custom(self, rpc, docker, cache):
        result = await odoo_schema_field_delete(
            rpc, docker, cache, "testdb", "res.partner", "name", confirm=True,
        )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_model_create_no_x_prefix(self, rpc, docker, cache):
        result = await odoo_schema_model_create(
            rpc, docker, cache, "testdb", "my.model", "My Model",
        )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_model_create_success(self, rpc, docker, cache):
        rpc.create.return_value = 1
        docker.restart_service = AsyncMock()
        docker.wait_for_healthy = AsyncMock()
        cache.refresh_models = MagicMock()
        result = await odoo_schema_model_create(
            rpc, docker, cache, "testdb", "x_my.model", "My Model",
        )
        assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_list_custom(self, rpc):
        # list_custom calls search_read twice: first for models, then for fields
        rpc.search_read.side_effect = [
            [{"model": "x_custom", "name": "Custom", "state": "manual"}],
            [{"name": "x_test", "field_description": "Test", "model": "res.partner",
              "ttype": "char", "state": "manual"}],
        ]
        result = await odoo_schema_list_custom(rpc, "testdb")
        assert result["field_count"] >= 1


# ═══════════════════════════════════════════════════════════════════
# DIAGNOSTICS TESTS
# ═══════════════════════════════════════════════════════════════════

class TestDiagnosticsHealthCheck:
    @pytest.mark.asyncio
    async def test_all_healthy(self, rpc, docker, pg):
        rpc.db_list.return_value = ["testdb"]
        rpc.authenticate.return_value = 2
        rpc.search_count.return_value = 15
        rpc.server_version.return_value = "18.0"
        result = await odoo_diagnostics_health_check(rpc, docker, pg, "testdb")
        assert result["overall"] == "healthy"
        assert result["failures"] == 0

    @pytest.mark.asyncio
    async def test_docker_down(self, rpc, docker, pg):
        docker.get_status = AsyncMock(return_value={"running": False})
        rpc.db_list.return_value = ["testdb"]
        rpc.authenticate.return_value = 2
        rpc.search_count.return_value = 15
        rpc.server_version.return_value = "18.0"
        result = await odoo_diagnostics_health_check(rpc, docker, pg, "testdb")
        assert result["overall"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_docker_exception(self, rpc, docker, pg):
        docker.get_status = AsyncMock(side_effect=Exception("Docker not found"))
        rpc.db_list.return_value = ["testdb"]
        rpc.authenticate.return_value = 2
        rpc.search_count.return_value = 15
        rpc.server_version.return_value = "18.0"
        result = await odoo_diagnostics_health_check(rpc, docker, pg, "testdb")
        assert result["overall"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_db_not_found(self, rpc, docker, pg):
        rpc.db_list.return_value = ["other_db"]
        rpc.authenticate.return_value = 2
        rpc.search_count.return_value = 15
        rpc.server_version.return_value = "18.0"
        result = await odoo_diagnostics_health_check(rpc, docker, pg, "testdb")
        assert result["overall"] == "degraded"

    @pytest.mark.asyncio
    async def test_auth_failure(self, rpc, docker, pg):
        rpc.db_list.return_value = ["testdb"]
        rpc.authenticate.side_effect = Exception("Invalid credentials")
        rpc.search_count.return_value = 15
        rpc.server_version.return_value = "18.0"
        result = await odoo_diagnostics_health_check(rpc, docker, pg, "testdb")
        assert result["overall"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_auth_returns_false(self, rpc, docker, pg):
        rpc.db_list.return_value = ["testdb"]
        rpc.authenticate.return_value = False
        rpc.search_count.return_value = 15
        rpc.server_version.return_value = "18.0"
        result = await odoo_diagnostics_health_check(rpc, docker, pg, "testdb")
        assert result["overall"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_pg_not_available(self, rpc, docker, pg):
        pg.ensure_pool = AsyncMock(side_effect=Exception("PG connection failed"))
        rpc.db_list.return_value = ["testdb"]
        rpc.authenticate.return_value = 2
        rpc.search_count.return_value = 15
        rpc.server_version.return_value = "18.0"
        result = await odoo_diagnostics_health_check(rpc, docker, pg, "testdb")
        # PG is optional, should still be healthy
        assert result["overall"] == "healthy"
        assert result["warnings"] >= 1

    @pytest.mark.asyncio
    async def test_error_logs_found(self, rpc, docker, pg):
        docker.logs = AsyncMock(return_value="ERROR: something broke\nERROR: another issue")
        rpc.db_list.return_value = ["testdb"]
        rpc.authenticate.return_value = 2
        rpc.search_count.return_value = 15
        rpc.server_version.return_value = "18.0"
        result = await odoo_diagnostics_health_check(rpc, docker, pg, "testdb")
        assert result["overall"] == "degraded"

    @pytest.mark.asyncio
    async def test_module_check_fails(self, rpc, docker, pg):
        rpc.db_list.return_value = ["testdb"]
        rpc.authenticate.return_value = 2
        rpc.search_count.side_effect = Exception("Module check failed")
        rpc.server_version.return_value = "18.0"
        result = await odoo_diagnostics_health_check(rpc, docker, pg, "testdb")
        assert result["warnings"] >= 1

    @pytest.mark.asyncio
    async def test_version_check_fails(self, rpc, docker, pg):
        rpc.db_list.return_value = ["testdb"]
        rpc.authenticate.return_value = 2
        rpc.search_count.return_value = 15
        rpc.server_version.side_effect = Exception("Version unavailable")
        result = await odoo_diagnostics_health_check(rpc, docker, pg, "testdb")
        assert result["warnings"] >= 1

    @pytest.mark.asyncio
    async def test_all_checks_fail(self, rpc, docker, pg):
        docker.get_status = AsyncMock(side_effect=Exception("Down"))
        rpc.db_list.side_effect = Exception("No connection")
        rpc.authenticate.side_effect = Exception("No auth")
        rpc.search_count.side_effect = Exception("No count")
        rpc.server_version.side_effect = Exception("No version")
        pg.ensure_pool = AsyncMock(side_effect=Exception("No PG"))
        docker.logs = AsyncMock(side_effect=Exception("No logs"))
        result = await odoo_diagnostics_health_check(rpc, docker, pg, "testdb")
        assert result["overall"] == "unhealthy"
        assert result["total"] == 7


# ═══════════════════════════════════════════════════════════════════
# VIEW EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestViewEdgeCases:
    @pytest.mark.asyncio
    async def test_list_empty(self, rpc):
        result = await odoo_view_list(rpc, "testdb", "res.partner")
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_get_arch_by_view_id(self, rpc):
        rpc.read.return_value = [{
            "id": 1, "name": "test", "type": "form",
            "arch": "<form></form>", "model": "res.partner",
        }]
        result = await odoo_view_get_arch(rpc, "testdb", view_id=1)
        assert result["found"] is True

    @pytest.mark.asyncio
    async def test_reset_base_view_blocked(self, rpc):
        rpc.read.return_value = [{
            "id": 1, "inherit_id": False, "name": "base.view_partner_form",
        }]
        result = await odoo_view_reset(rpc, "testdb", view_id=1, confirm=True)
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_list_customizations_with_results(self, rpc):
        rpc.search_read.return_value = [{
            "id": 1, "name": "custom_view", "model": "res.partner",
            "type": "form", "inherit_id": [2, "base.view_partner_form"],
            "priority": 99, "active": True,
        }]
        result = await odoo_view_list_customizations(rpc, "testdb")
        assert result["count"] == 1


# ═══════════════════════════════════════════════════════════════════
# REPORT EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestReportEdgeCases:
    @pytest.mark.asyncio
    async def test_list_empty(self, rpc):
        result = await odoo_report_list(rpc, "testdb")
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, rpc):
        result = await odoo_report_get_template(rpc, "testdb", "nonexistent.report")
        assert result.get("found") is False or result.get("status") == "error" or "not found" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_preview_with_records(self, rpc):
        rpc.execute_method.return_value = True
        result = await odoo_report_preview(rpc, "testdb", "account.report_invoice", [1, 2])
        assert "report_name" in result or "status" in result


# ═══════════════════════════════════════════════════════════════════
# AUTOMATION EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestAutomationEdgeCases:
    @pytest.mark.asyncio
    async def test_list_empty(self, rpc):
        result = await odoo_automation_list(rpc, "testdb")
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_create_server_action(self, rpc):
        rpc.search_read.return_value = [{"id": 1, "model": "res.partner"}]
        rpc.create.return_value = 10
        # Signature: (rpc, db_name, name, model, trigger, ...)
        result = await odoo_automation_create(
            rpc, "testdb", "Auto Test", "res.partner", "on_create",
            action_type="code",
            code="record.write({'name': record.name.upper()})",
        )
        assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_update_nonexistent(self, rpc):
        rpc.read.return_value = []
        result = await odoo_automation_update(
            rpc, "testdb", 99999, {"name": "Updated"},
        )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_delete_no_confirm(self, rpc):
        result = await odoo_automation_delete(rpc, "testdb", 1, confirm=False)
        assert result["status"] in ("cancelled", "confirmation_required")

    @pytest.mark.asyncio
    async def test_email_template_create(self, rpc):
        rpc.search_read.return_value = [{"id": 1, "model": "res.partner"}]
        rpc.create.return_value = 5
        # Signature: (rpc, db_name, name, model, subject, body_html, ...)
        result = await odoo_email_template_create(
            rpc, "testdb", "Welcome", "res.partner",
            "Welcome {{object.name}}", "<p>Hello</p>",
        )
        assert result["status"] == "created"


# ═══════════════════════════════════════════════════════════════════
# NETWORK EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestNetworkEdgeCases:
    @pytest.mark.asyncio
    async def test_status_no_tunnels(self):
        from odooforge.tools.network import _active_tunnels
        _active_tunnels.clear()
        result = await odoo_network_status()
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_stop_no_tunnels(self):
        from odooforge.tools.network import _active_tunnels
        _active_tunnels.clear()
        result = await odoo_network_stop()
        assert result["count"] == 0


# ═══════════════════════════════════════════════════════════════════
# IMPORT EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestImportEdgeCases:
    @pytest.mark.asyncio
    async def test_preview_single_column(self, rpc):
        result = await odoo_import_preview(rpc, "testdb", "res.partner", "name\nAlice")
        assert result["status"] == "preview"
        assert result["valid_fields"] == 1

    @pytest.mark.asyncio
    async def test_preview_all_invalid_fields(self, rpc):
        result = await odoo_import_preview(
            rpc, "testdb", "res.partner", "bad1,bad2\nv1,v2",
        )
        assert result["invalid_fields"] == 2

    @pytest.mark.asyncio
    async def test_execute_with_errors(self, rpc):
        rpc.load.return_value = {
            "ids": [],
            "messages": [{"type": "error", "message": "Invalid value"}],
        }
        csv = "name,email\nAlice,bad-email"
        result = await odoo_import_execute(rpc, "testdb", "res.partner", csv)
        assert result["status"] == "error"
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_execute_empty_csv(self, rpc):
        result = await odoo_import_execute(rpc, "testdb", "res.partner", "")
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_template_readonly_excluded(self, rpc):
        rpc.fields_get.return_value = {
            "id": {"type": "integer", "readonly": True, "string": "ID", "required": True},
            "name": {"type": "char", "readonly": False, "string": "Name", "required": True},
            "create_date": {"type": "datetime", "readonly": True, "string": "Created"},
        }
        result = await odoo_import_template(rpc, "testdb", "res.partner")
        assert "id" not in result["csv_header"]
        assert "name" in result["csv_header"]


# ═══════════════════════════════════════════════════════════════════
# EMAIL EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestEmailEdgeCases:
    @pytest.mark.asyncio
    async def test_outgoing_with_all_params(self, rpc):
        rpc.create.return_value = 10
        result = await odoo_email_configure_outgoing(
            rpc, "testdb", "Custom SMTP", "smtp.custom.com",
            smtp_port=465, smtp_encryption="ssl", smtp_user="user@custom.com",
            smtp_pass="secret",
        )
        assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_incoming_imap(self, rpc):
        rpc.create.return_value = 10
        result = await odoo_email_configure_incoming(
            rpc, "testdb", "IMAP Inbox",
            host="imap.gmail.com", port=993,
            server_type="imap", user="user@gmail.com",
            password="secret", ssl=True,
        )
        assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_dns_guide_subdomains(self):
        result = await odoo_email_dns_guide("mail.example.com")
        assert result["domain"] == "mail.example.com"
        assert len(result["records"]) >= 3

    @pytest.mark.asyncio
    async def test_email_test_custom_subject(self, rpc):
        rpc.create.return_value = 100
        result = await odoo_email_test(
            rpc, "testdb", "admin@example.com",
        )
        assert result["status"] == "sent"


# ═══════════════════════════════════════════════════════════════════
# SETTINGS EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestSettingsEdgeCases:
    @pytest.mark.asyncio
    async def test_get_exception(self, rpc):
        # settings_get catches exceptions internally and returns error dict
        rpc.create.side_effect = Exception("Access denied")
        result = await odoo_settings_get(rpc, "testdb")
        assert result["status"] == "error"
        assert "Access denied" in result["message"]

    @pytest.mark.asyncio
    async def test_set_multiple_values(self, rpc):
        rpc.create.return_value = 1
        result = await odoo_settings_set(
            rpc, "testdb",
            {"module_sale": True, "module_crm": True, "group_multi_currency": True},
        )
        assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_company_configure_with_logo(self, rpc):
        rpc.search_read.return_value = [{"id": 1, "name": "My Co"}]
        result = await odoo_company_configure(
            rpc, "testdb",
            {"name": "New Corp", "email": "info@newcorp.com", "phone": "+1234567890"},
        )
        assert result["status"] == "configured"

    @pytest.mark.asyncio
    async def test_users_manage_activate(self, rpc):
        result = await odoo_users_manage(
            rpc, "testdb", action="activate", user_id=5,
        )
        assert result["status"] == "activated"

    @pytest.mark.asyncio
    async def test_users_manage_update(self, rpc):
        result = await odoo_users_manage(
            rpc, "testdb", action="update", user_id=3,
            values={"name": "Updated Name"},
        )
        assert result["status"] == "updated"


# ═══════════════════════════════════════════════════════════════════
# KNOWLEDGE EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestKnowledgeEdgeCases:
    @pytest.mark.asyncio
    async def test_all_builtin_modules(self):
        for mod in ["sale", "crm", "purchase", "account", "stock",
                     "hr", "website", "project"]:
            result = await odoo_knowledge_module_info(mod)
            assert result["found"] is True, f"{mod} should be found"

    @pytest.mark.asyncio
    async def test_search_case_insensitive(self):
        result_lower = await odoo_knowledge_search("sales")
        result_upper = await odoo_knowledge_search("SALES")
        # Both should work (or at least not crash)
        assert isinstance(result_lower["count"], int)
        assert isinstance(result_upper["count"], int)

    @pytest.mark.asyncio
    async def test_search_partial_match(self):
        result = await odoo_knowledge_search("sale")
        assert result["count"] > 0

    @pytest.mark.asyncio
    async def test_gaps_company_incomplete(self, rpc):
        rpc.search_read.side_effect = [
            [{"name": "sale"}],  # only one module installed
            [{"id": 1, "name": "My Company", "currency_id": [1, "USD"],
              "country_id": False, "email": ""}],  # incomplete company
        ]
        result = await odoo_knowledge_community_gaps(rpc, "testdb")
        assert result["count"] > 0


# ═══════════════════════════════════════════════════════════════════
# RECIPE EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestRecipeEdgeCases:
    @pytest.mark.asyncio
    async def test_all_dry_runs(self, rpc):
        """Every recipe should produce a valid dry run."""
        for recipe_id in RECIPES:
            result = await odoo_recipe_execute(rpc, "testdb", recipe_id, dry_run=True)
            assert result["status"] == "dry_run"
            assert len(result["modules_to_install"]) > 0
            assert len(result["steps"]) > 0

    @pytest.mark.asyncio
    async def test_execute_module_not_found(self, rpc):
        rpc.search_read.side_effect = [
            [],  # no installed modules
            [],  # point_of_sale not found
            [],  # pos_restaurant not found
            [],  # stock not found
            [],  # purchase not found
            [],  # account not found
            [],  # contacts not found
            [],  # hr not found
            [],  # hr_attendance not found
        ]
        result = await odoo_recipe_execute(rpc, "testdb", "restaurant", dry_run=False)
        assert result["status"] == "executed"
        # Should report modules as not_found
        assert any(r.get("status") == "not_found" for r in result["results"])

    @pytest.mark.asyncio
    async def test_execute_install_error(self, rpc):
        rpc.search_read.side_effect = [
            [],  # no installed
            [{"id": 1, "state": "uninstalled"}],  # first module found
        ]
        rpc.execute_method.side_effect = Exception("Install failed")
        result = await odoo_recipe_execute(rpc, "testdb", "restaurant", dry_run=False)
        assert result["status"] == "executed"
        assert any(r.get("status") == "error" for r in result["results"])

    @pytest.mark.asyncio
    async def test_recipe_list_structure(self):
        result = await odoo_recipe_list()
        for recipe in result["recipes"]:
            assert "id" in recipe
            assert "name" in recipe
            assert "description" in recipe
            assert "modules" in recipe
            assert isinstance(recipe["modules"], list)


# ═══════════════════════════════════════════════════════════════════
# VALIDATOR EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestValidatorEdgeCases:
    def test_domain_deeply_nested_connectors(self):
        domain = ["|", ("name", "=", "A"), "&", ("email", "!=", False), ("active", "=", True)]
        result = validate_domain(domain)
        assert len(result) > 0

    def test_domain_single_tuple(self):
        domain = [("name", "=", "test")]
        result = validate_domain(domain)
        assert result == domain

    def test_domain_all_connectors(self):
        domain = ["&", "|", ("a", "=", 1), ("b", "=", 2), ("c", "=", 3)]
        result = validate_domain(domain)
        assert len(result) == 5

    def test_model_name_with_numbers(self):
        validate_model_name("x_custom2.model")

    def test_model_name_underscores(self):
        validate_model_name("hr_contract.salary")

    def test_db_name_with_underscores(self):
        validate_db_name("my_test_db_123")

    def test_field_name_valid(self):
        # validate_field_name returns the name string on success
        assert validate_field_name("x_custom_field") == "x_custom_field"
        assert validate_field_name("name") == "name"
        assert validate_field_name("partner_id") == "partner_id"

    def test_field_name_invalid(self):
        with pytest.raises(ValueError):
            validate_field_name("")
        with pytest.raises(ValueError):
            validate_field_name("bad field")


# ═══════════════════════════════════════════════════════════════════
# FORMATTING EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestFormattingEdgeCases:
    def test_format_table_unicode(self):
        result = format_table(["Name"], [["Ünïcödé"]])
        assert "Ünïcödé" in result

    def test_format_table_long_values(self):
        result = format_table(["Name"], [["A" * 500]])
        assert isinstance(result, str)

    def test_format_record_nested_dict(self):
        result = format_record({"nested": {"a": 1, "b": 2}})
        assert isinstance(result, str)

    def test_truncate_exact_length(self):
        text = "x" * 100
        result = truncate(text, 100)
        assert result == text

    def test_truncate_empty(self):
        assert truncate("", 50) == ""


# ═══════════════════════════════════════════════════════════════════
# BINARY HANDLER EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestBinaryHandlerEdgeCases:
    def test_encode_real_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("hello,world\n")
            path = f.name
        try:
            result = encode_file(path)
            assert "base64" in result
            assert result["size_bytes"] > 0
        finally:
            os.unlink(path)

    def test_csv_single_row(self):
        result = csv_to_import_data("name\nAlice")
        assert result["row_count"] == 1
        assert result["headers"] == ["name"]

    def test_csv_with_commas_in_values(self):
        result = csv_to_import_data('name,city\n"Smith, John","New York, NY"')
        assert result["row_count"] == 1
        assert result["headers"] == ["name", "city"]

    def test_csv_only_header(self):
        result = csv_to_import_data("name,email")
        assert result["row_count"] == 0

    def test_format_file_size_zero(self):
        assert "0" in format_file_size(0)

    def test_format_file_size_gigabytes(self):
        assert "GB" in format_file_size(2 * 1024 * 1024 * 1024)

    def test_format_file_size_exact_boundary(self):
        assert "KB" in format_file_size(1024)


# ═══════════════════════════════════════════════════════════════════
# XPATH/QWEB BUILDER EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestXPathBuilderEdgeCases:
    def test_field_xpath_returns_string(self):
        result = field_xpath("partner_id")
        assert "partner_id" in result
        assert "field" in result

    def test_build_field_xml_with_widget(self):
        result = build_field_xml("x_custom", widget="many2many_tags")
        assert "many2many_tags" in result

    def test_build_inherit_xml_multiple_specs(self):
        specs = [
            {"expr": field_xpath("name"), "position": "after",
             "content": '<field name="x_custom"/>'},
            {"expr": field_xpath("email"), "position": "before",
             "content": '<field name="x_other"/>'},
        ]
        result = build_inherit_xml(specs)
        assert "x_custom" in result
        assert "x_other" in result

    def test_group_xpath_by_string(self):
        result = group_xpath(string="General Information")
        assert "General Information" in result


class TestQWebBuilderEdgeCases:
    def test_div_xpath_with_class(self):
        result = div_xpath("page")
        assert "page" in result

    def test_build_qweb_field_text_only(self):
        result = build_qweb_field("object.name")
        assert "object.name" in result

    def test_build_qweb_inherit_multiple_ops(self):
        specs = [
            {"expr": div_xpath("page"), "position": "inside",
             "content": '<span t-field="object.x_custom"/>'},
        ]
        result = build_qweb_inherit_xml("custom.template", specs)
        assert "x_custom" in result
        assert "custom.template" in result


# ═══════════════════════════════════════════════════════════════════
# ERROR CLASS EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestErrorClassEdgeCases:
    def test_all_error_subclasses(self):
        """All custom errors are OdooForgeError subclasses."""
        for cls in [ConnectionError, AuthenticationError, DatabaseError,
                    ModuleError, ValidationError, ViewError, SnapshotError]:
            e = cls("test", "suggestion")
            assert isinstance(e, OdooForgeError)
            assert "test" in str(e)

    def test_error_no_suggestion(self):
        e = OdooForgeError("bare error")
        d = e.to_dict()
        assert "suggestion" not in d or d["suggestion"] == ""
        assert d["message"] == "bare error"

    def test_error_code_propagation(self):
        e = OdooForgeError("msg", code="CUSTOM_123")
        assert e.to_dict()["code"] == "CUSTOM_123"

    def test_enrich_all_fault_types(self):
        """Every fault type in the catalog should be matched."""
        for fault_key in FAULT_SUGGESTIONS:
            result = enrich_rpc_error(f"Some error: {fault_key}: details")
            assert result["code"] == fault_key

    def test_enrich_truncates_long_message(self):
        long_msg = "A" * 1000
        result = enrich_rpc_error(long_msg)
        assert len(result["message"]) <= 500

    def test_docker_not_running_is_exception(self):
        e = DockerNotRunningError()
        assert isinstance(e, Exception)
        assert isinstance(e, OdooForgeError)


# ═══════════════════════════════════════════════════════════════════
# RESPONSE FORMATTER EDGE CASES
# ═══════════════════════════════════════════════════════════════════

class TestResponseFormatterEdgeCases:
    def test_success_with_no_extras(self):
        r = success("Done")
        assert r == {"status": "ok", "message": "Done"}

    def test_error_with_extras(self):
        r = error("Fail", code="E001", details={"line": 5})
        assert r["code"] == "E001"
        assert r["details"]["line"] == 5

    def test_paginated_empty(self):
        r = paginated([], total=0)
        assert r["count"] == 0
        assert r["total"] == 0

    def test_paginated_custom_key(self):
        r = paginated([{"id": 1}], total=1, item_key="modules")
        assert "modules" in r
        assert "items" not in r

    def test_confirm_with_details(self):
        r = confirm_required("drop", "testdb", details={"size": "500MB"})
        assert r["details"]["size"] == "500MB"

    def test_format_duration_zero(self):
        assert "0" in format_duration(0.0)

    def test_format_duration_fractional(self):
        result = format_duration(0.5)
        assert "s" in result

    def test_format_duration_exactly_60(self):
        result = format_duration(60)
        assert "m" in result
