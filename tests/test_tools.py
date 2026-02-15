"""Tests for record CRUD tools with mocked RPC + cache."""

import pytest
from unittest.mock import MagicMock

from odooforge.tools.records import (
    odoo_record_search,
    odoo_record_read,
    odoo_record_create,
    odoo_record_update,
    odoo_record_delete,
    odoo_record_execute,
)


@pytest.fixture
def rpc():
    mock = MagicMock()
    mock.search_read.return_value = [{"id": 1, "name": "Test"}]
    mock.search_count.return_value = 1
    mock.read.return_value = [{"id": 1, "name": "Test"}]
    mock.create.return_value = 42
    mock.write.return_value = True
    mock.unlink.return_value = True
    mock.execute_method.return_value = {"result": "ok"}
    return mock


@pytest.fixture
def cache():
    mock = MagicMock()
    mock.validate_fields.return_value = []  # No invalid fields
    mock.get_model_fields.return_value = {"name": {}, "email": {}}
    return mock


class TestRecordSearch:
    @pytest.mark.asyncio
    async def test_basic_search(self, rpc):
        result = await odoo_record_search(rpc, "testdb", "res.partner")
        assert result["count"] == 1
        assert result["total"] == 1
        assert result["records"][0]["name"] == "Test"

    @pytest.mark.asyncio
    async def test_search_with_domain(self, rpc):
        result = await odoo_record_search(
            rpc, "testdb", "res.partner",
            domain=[("is_company", "=", True)],
        )
        rpc.search_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_limit_cap(self, rpc):
        await odoo_record_search(rpc, "testdb", "res.partner", limit=500)
        call_kwargs = rpc.search_read.call_args
        # limit should be capped at 200
        assert call_kwargs.kwargs.get("limit", call_kwargs[1].get("limit")) <= 200

    @pytest.mark.asyncio
    async def test_search_pagination_info(self, rpc):
        rpc.search_count.return_value = 100
        rpc.search_read.return_value = [{"id": i} for i in range(20)]
        result = await odoo_record_search(rpc, "testdb", "res.partner", limit=20)
        assert result["has_more"] is True
        assert result["total"] == 100

    @pytest.mark.asyncio
    async def test_invalid_model(self, rpc):
        with pytest.raises(ValueError, match="dot-separated"):
            await odoo_record_search(rpc, "testdb", "partner")


class TestRecordRead:
    @pytest.mark.asyncio
    async def test_read_by_ids(self, rpc):
        result = await odoo_record_read(rpc, "testdb", "res.partner", [1])
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_read_empty_ids(self, rpc):
        result = await odoo_record_read(rpc, "testdb", "res.partner", [])
        assert result["count"] == 0


class TestRecordCreate:
    @pytest.mark.asyncio
    async def test_create_single(self, rpc, cache):
        result = await odoo_record_create(
            rpc, cache, "testdb", "res.partner",
            {"name": "New Partner"},
        )
        assert result["status"] == "created"
        assert result["ids"] == [42]

    @pytest.mark.asyncio
    async def test_create_multiple(self, rpc, cache):
        rpc.create.return_value = [10, 11]
        result = await odoo_record_create(
            rpc, cache, "testdb", "res.partner",
            [{"name": "A"}, {"name": "B"}],
        )
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_create_invalid_fields(self, rpc, cache):
        cache.validate_fields.return_value = ["nonexistent_field"]
        result = await odoo_record_create(
            rpc, cache, "testdb", "res.partner",
            {"nonexistent_field": "value"},
        )
        assert result["status"] == "error"
        assert "nonexistent_field" in result["invalid_fields"]


class TestRecordUpdate:
    @pytest.mark.asyncio
    async def test_update(self, rpc, cache):
        result = await odoo_record_update(
            rpc, cache, "testdb", "res.partner", [1], {"name": "Updated"},
        )
        assert result["status"] == "updated"
        assert result["updated_count"] == 1

    @pytest.mark.asyncio
    async def test_update_no_ids(self, rpc, cache):
        result = await odoo_record_update(rpc, cache, "testdb", "res.partner", [], {"name": "X"})
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_update_invalid_fields(self, rpc, cache):
        cache.validate_fields.return_value = ["bad"]
        result = await odoo_record_update(
            rpc, cache, "testdb", "res.partner", [1], {"bad": "val"},
        )
        assert result["status"] == "error"


class TestRecordDelete:
    @pytest.mark.asyncio
    async def test_delete_without_confirm(self, rpc):
        result = await odoo_record_delete(rpc, "testdb", "res.partner", [1])
        assert result["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_delete_confirmed(self, rpc):
        result = await odoo_record_delete(rpc, "testdb", "res.partner", [1], confirm=True)
        assert result["status"] == "deleted"
        assert result["deleted_count"] == 1


class TestRecordExecute:
    @pytest.mark.asyncio
    async def test_execute_method(self, rpc):
        result = await odoo_record_execute(
            rpc, "testdb", "res.partner", "check_access_rights",
            args=["read"], kwargs={"raise_exception": False},
        )
        assert result["method"] == "check_access_rights"
        assert result["result"] == {"result": "ok"}
