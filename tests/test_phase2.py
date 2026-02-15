"""Tests for Phase 2 tools: snapshots, modules, models, schema."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from odooforge.tools.snapshots import (
    odoo_snapshot_create, odoo_snapshot_list,
    odoo_snapshot_restore, odoo_snapshot_delete,
)
from odooforge.tools.modules import (
    odoo_module_list_available, odoo_module_list_installed,
    odoo_module_info, odoo_module_install,
    odoo_module_upgrade, odoo_module_uninstall,
)
from odooforge.tools.models import (
    odoo_model_list, odoo_model_fields, odoo_model_search_field,
)
from odooforge.tools.schema import (
    odoo_schema_field_create, odoo_schema_field_update,
    odoo_schema_field_delete, odoo_schema_model_create,
    odoo_schema_list_custom,
)


# ── Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def rpc():
    m = MagicMock()
    m.search_read.return_value = []
    m.fields_get.return_value = {}
    m.read.return_value = []
    m.create.return_value = 1
    m.write.return_value = True
    m.unlink.return_value = True
    m.search_count.return_value = 0
    m.execute_method.return_value = True
    m.authenticate.return_value = 2
    return m


@pytest.fixture
def docker():
    m = MagicMock()
    m.create_snapshot = AsyncMock(return_value={
        "name": "snap1", "size_bytes": 1024 * 1024, "created_at": "2024-01-01",
    })
    m.list_snapshots = AsyncMock(return_value=[])
    m.restore_snapshot = AsyncMock()
    m.delete_snapshot = AsyncMock(return_value={"freed_bytes": 512000})
    m.restart_service = AsyncMock()
    m.wait_for_healthy = AsyncMock()
    m.install_module_via_cli = AsyncMock(return_value="OK")
    m.upgrade_module_via_cli = AsyncMock(return_value="OK")
    m.logs = AsyncMock(return_value="")
    return m


@pytest.fixture
def cache():
    m = MagicMock()
    m.refresh_all.return_value = None
    m.refresh_modules.return_value = {}
    m.refresh_model_fields.return_value = {}
    m.refresh_models.return_value = {}
    m.is_field_valid.return_value = False
    m.validate_fields.return_value = []
    m.get_model_fields.return_value = None
    return m


# ── Snapshot Tests ─────────────────────────────────────────────────

class TestSnapshotCreate:
    @pytest.mark.asyncio
    async def test_create_success(self, docker):
        result = await odoo_snapshot_create(docker, "mydb", "snap1")
        assert result["status"] == "created"
        assert result["snapshot"] == "snap1"
        assert result["size_mb"] == 1.0

    @pytest.mark.asyncio
    async def test_create_empty_name(self, docker):
        result = await odoo_snapshot_create(docker, "mydb", "")
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_create_duplicate(self, docker):
        docker.list_snapshots = AsyncMock(return_value=[{"name": "snap1"}])
        result = await odoo_snapshot_create(docker, "mydb", "snap1")
        assert result["status"] == "error"
        assert "already exists" in result["message"]


class TestSnapshotList:
    @pytest.mark.asyncio
    async def test_list_empty(self, docker):
        result = await odoo_snapshot_list(docker)
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_list_with_data(self, docker):
        docker.list_snapshots = AsyncMock(return_value=[
            {"name": "s1", "database": "db1", "created_at": "2024-01-01", "size_bytes": 2048},
        ])
        result = await odoo_snapshot_list(docker, db_name="db1")
        assert result["count"] == 1
        assert result["snapshots"][0]["name"] == "s1"


class TestSnapshotRestore:
    @pytest.mark.asyncio
    async def test_restore_success(self, docker, rpc, cache):
        result = await odoo_snapshot_restore(docker, rpc, cache, "mydb", "snap1")
        assert result["status"] == "restored"
        docker.restore_snapshot.assert_called_once()


class TestSnapshotDelete:
    @pytest.mark.asyncio
    async def test_delete(self, docker):
        result = await odoo_snapshot_delete(docker, "snap1")
        assert result["status"] == "deleted"
        assert result["freed_mb"] > 0


# ── Module Tests ───────────────────────────────────────────────────

class TestModuleListAvailable:
    @pytest.mark.asyncio
    async def test_list_all(self, rpc):
        rpc.search_read.return_value = [
            {"name": "sale", "shortdesc": "Sales", "state": "uninstalled",
             "category_id": [1, "Sales"], "summary": "Manage sales", "latest_version": "18.0.1"},
        ]
        result = await odoo_module_list_available(rpc, "testdb")
        assert result["count"] == 1
        assert result["modules"][0]["name"] == "sale"


class TestModuleListInstalled:
    @pytest.mark.asyncio
    async def test_list(self, rpc):
        rpc.search_read.return_value = [
            {"name": "base", "shortdesc": "Base", "latest_version": "18.0", "category_id": [1, "Hidden"]},
        ]
        result = await odoo_module_list_installed(rpc, "testdb")
        assert result["count"] == 1


class TestModuleInfo:
    @pytest.mark.asyncio
    async def test_found(self, rpc):
        rpc.search_read.return_value = [{
            "name": "sale", "shortdesc": "Sales", "state": "installed",
            "latest_version": "18.0.1", "category_id": [1, "Sales"],
            "summary": "Manage sales", "description": "Full desc",
            "author": "Odoo SA", "website": "https://odoo.com",
            "dependencies_id": [],
        }]
        result = await odoo_module_info(rpc, "testdb", "sale")
        assert result["found"] is True
        assert result["name"] == "sale"

    @pytest.mark.asyncio
    async def test_not_found(self, rpc):
        rpc.search_read.return_value = []
        result = await odoo_module_info(rpc, "testdb", "nonexistent")
        assert result["found"] is False


class TestModuleInstall:
    @pytest.mark.asyncio
    async def test_install_new(self, rpc, docker, cache):
        rpc.search_read.side_effect = [
            [{"name": "sale", "state": "uninstalled"}],  # Check if installed
            [{"name": "sale", "state": "installed", "shortdesc": "Sales", "latest_version": "18.0"}],  # Verify
        ]
        result = await odoo_module_install(rpc, docker, cache, "testdb", ["sale"])
        assert result["status"] in ("installed", "installed_with_issues")
        assert "sale" in result["installed"]

    @pytest.mark.asyncio
    async def test_install_already_installed(self, rpc, docker, cache):
        rpc.search_read.return_value = [{"name": "base", "state": "installed"}]
        result = await odoo_module_install(rpc, docker, cache, "testdb", ["base"])
        assert result["status"] == "already_installed"

    @pytest.mark.asyncio
    async def test_install_empty(self, rpc, docker, cache):
        result = await odoo_module_install(rpc, docker, cache, "testdb", [])
        assert result["status"] == "error"


class TestModuleUninstall:
    @pytest.mark.asyncio
    async def test_uninstall_no_confirm(self, rpc, docker, cache):
        result = await odoo_module_uninstall(rpc, docker, cache, "testdb", "sale")
        assert result["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_uninstall_confirmed(self, rpc, docker, cache):
        rpc.search_read.return_value = [{"id": 5, "state": "installed"}]
        result = await odoo_module_uninstall(rpc, docker, cache, "testdb", "sale", confirm=True)
        assert result["status"] == "uninstalled"


# ── Model Tests ────────────────────────────────────────────────────

class TestModelList:
    @pytest.mark.asyncio
    async def test_list_models(self, rpc):
        rpc.search_read.return_value = [
            {"model": "res.partner", "name": "Contact", "state": "base", "transient": False, "count": 100},
        ]
        result = await odoo_model_list(rpc, "testdb")
        assert result["count"] == 1
        assert result["models"][0]["model"] == "res.partner"


class TestModelFields:
    @pytest.mark.asyncio
    async def test_get_fields(self, rpc, cache):
        rpc.fields_get.return_value = {
            "name": {"string": "Name", "type": "char", "required": True, "readonly": False, "store": True},
            "email": {"string": "Email", "type": "char", "required": False, "readonly": False, "store": True},
        }
        result = await odoo_model_fields(rpc, cache, "testdb", "res.partner")
        assert result["count"] == 2
        assert result["model"] == "res.partner"

    @pytest.mark.asyncio
    async def test_filter_by_type(self, rpc, cache):
        rpc.fields_get.return_value = {
            "name": {"string": "Name", "type": "char", "required": True, "readonly": False, "store": True},
            "active": {"string": "Active", "type": "boolean", "required": False, "readonly": False, "store": True},
        }
        result = await odoo_model_fields(rpc, cache, "testdb", "res.partner", field_type="boolean")
        assert result["count"] == 1
        assert result["fields"][0]["name"] == "active"


class TestModelSearchField:
    @pytest.mark.asyncio
    async def test_search(self, rpc):
        rpc.search_read.return_value = [
            {"name": "email", "field_description": "Email", "model": "res.partner",
             "ttype": "char", "relation": "", "required": False, "store": True},
        ]
        result = await odoo_model_search_field(rpc, "testdb", "email")
        assert result["count"] == 1
        assert result["results"][0]["field"] == "email"


# ── Schema Tests ───────────────────────────────────────────────────

class TestSchemaFieldCreate:
    @pytest.mark.asyncio
    async def test_create_success(self, rpc, docker, cache):
        rpc.search_read.return_value = [{"id": 10}]  # model lookup
        rpc.create.return_value = 42
        cache.is_field_valid.side_effect = [False, True]  # Not exists, then verified
        result = await odoo_schema_field_create(
            rpc, docker, cache, "testdb", "res.partner",
            "x_loyalty", "char", "Loyalty Status",
        )
        assert result["status"] == "created"
        assert result["field_id"] == 42

    @pytest.mark.asyncio
    async def test_create_no_x_prefix(self, rpc, docker, cache):
        result = await odoo_schema_field_create(
            rpc, docker, cache, "testdb", "res.partner",
            "loyalty", "char", "Loyalty",
        )
        assert result["status"] == "error"
        assert "x_" in result["message"]

    @pytest.mark.asyncio
    async def test_create_invalid_type(self, rpc, docker, cache):
        result = await odoo_schema_field_create(
            rpc, docker, cache, "testdb", "res.partner",
            "x_bad", "invalid_type", "Bad",
        )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_relational_without_relation(self, rpc, docker, cache):
        result = await odoo_schema_field_create(
            rpc, docker, cache, "testdb", "res.partner",
            "x_rel", "many2one", "Related",
        )
        assert result["status"] == "error"
        assert "relation_model" in result["message"]

    @pytest.mark.asyncio
    async def test_already_exists(self, rpc, docker, cache):
        cache.is_field_valid.return_value = True
        result = await odoo_schema_field_create(
            rpc, docker, cache, "testdb", "res.partner",
            "x_existing", "char", "Existing",
        )
        assert result["status"] == "already_exists"


class TestSchemaFieldUpdate:
    @pytest.mark.asyncio
    async def test_update_success(self, rpc, cache):
        rpc.search_read.return_value = [{"id": 5}]
        result = await odoo_schema_field_update(
            rpc, cache, "testdb", "res.partner", "x_test",
            {"field_description": "Updated Label"},
        )
        assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_update_non_custom(self, rpc, cache):
        result = await odoo_schema_field_update(
            rpc, cache, "testdb", "res.partner", "name", {},
        )
        assert result["status"] == "error"


class TestSchemaFieldDelete:
    @pytest.mark.asyncio
    async def test_delete_no_confirm(self, rpc, docker, cache):
        result = await odoo_schema_field_delete(
            rpc, docker, cache, "testdb", "res.partner", "x_test",
        )
        assert result["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_delete_confirmed(self, rpc, docker, cache):
        rpc.search_read.return_value = [{"id": 5}]
        result = await odoo_schema_field_delete(
            rpc, docker, cache, "testdb", "res.partner", "x_test", confirm=True,
        )
        assert result["status"] == "deleted"


class TestSchemaModelCreate:
    @pytest.mark.asyncio
    async def test_create_model(self, rpc, docker, cache):
        rpc.create.return_value = 100
        result = await odoo_schema_model_create(
            rpc, docker, cache, "testdb", "x_loyalty.program", "Loyalty Program",
        )
        assert result["status"] == "created"
        assert result["model_name"] == "x_loyalty.program"

    @pytest.mark.asyncio
    async def test_create_no_x_prefix(self, rpc, docker, cache):
        result = await odoo_schema_model_create(
            rpc, docker, cache, "testdb", "loyalty.program", "Loyalty",
        )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_create_with_fields(self, rpc, docker, cache):
        rpc.create.return_value = 100
        result = await odoo_schema_model_create(
            rpc, docker, cache, "testdb", "x_test.model", "Test",
            fields=[{"name": "x_code", "type": "char", "label": "Code"}],
        )
        assert result["fields_created"] == 1


class TestSchemaListCustom:
    @pytest.mark.asyncio
    async def test_list_custom(self, rpc):
        rpc.search_read.side_effect = [
            [{"model": "x_test.model", "name": "Test"}],  # models
            [{"name": "x_field", "field_description": "Field", "model": "res.partner", "ttype": "char"}],  # fields
        ]
        result = await odoo_schema_list_custom(rpc, "testdb")
        assert result["model_count"] == 1
        assert result["field_count"] == 1
