"""Tests for Phase 5 tools: recipes, response formatting, error handling."""

import pytest
from unittest.mock import MagicMock

from odooforge.tools.recipes import odoo_recipe_list, odoo_recipe_execute, RECIPES
from odooforge.utils.response_formatter import (
    success, error, paginated, confirm_required, format_duration,
)
from odooforge.utils.errors import (
    OdooForgeError, DockerNotRunningError, enrich_rpc_error,
)


# ── Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def rpc():
    m = MagicMock()
    m.search_read.return_value = []
    m.create.return_value = 1
    m.execute_method.return_value = True
    return m


# ── Recipe Tests ──────────────────────────────────────────────────

class TestRecipeList:
    @pytest.mark.asyncio
    async def test_list(self):
        result = await odoo_recipe_list()
        assert result["count"] == 5
        ids = [r["id"] for r in result["recipes"]]
        assert "restaurant" in ids
        assert "ecommerce" in ids
        assert "manufacturing" in ids
        assert "services" in ids
        assert "retail" in ids


class TestRecipeExecute:
    @pytest.mark.asyncio
    async def test_dry_run(self, rpc):
        result = await odoo_recipe_execute(rpc, "testdb", "restaurant", dry_run=True)
        assert result["status"] == "dry_run"
        assert len(result["modules_to_install"]) > 0

    @pytest.mark.asyncio
    async def test_unknown_recipe(self, rpc):
        result = await odoo_recipe_execute(rpc, "testdb", "nonexistent")
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_execute(self, rpc):
        rpc.search_read.side_effect = [
            [],  # installed modules
            [{"id": 1, "state": "uninstalled"}],  # point_of_sale
            [{"id": 2, "state": "uninstalled"}],  # pos_restaurant
            [{"id": 3, "state": "uninstalled"}],  # stock
            [{"id": 4, "state": "uninstalled"}],  # purchase
            [{"id": 5, "state": "uninstalled"}],  # account
            [{"id": 6, "state": "uninstalled"}],  # contacts
            [{"id": 7, "state": "uninstalled"}],  # hr
            [{"id": 8, "state": "uninstalled"}],  # hr_attendance
        ]
        result = await odoo_recipe_execute(rpc, "testdb", "restaurant", dry_run=False)
        assert result["status"] == "executed"

    @pytest.mark.asyncio
    async def test_all_recipes_have_fields(self):
        for key, recipe in RECIPES.items():
            assert "name" in recipe, f"{key} missing name"
            assert "modules" in recipe, f"{key} missing modules"
            assert "steps" in recipe, f"{key} missing steps"


# ── Response Formatter Tests ──────────────────────────────────────

class TestResponseFormatter:
    def test_success(self):
        r = success("Done", count=5)
        assert r["status"] == "ok"
        assert r["count"] == 5

    def test_error_with_suggestion(self):
        r = error("Failed", suggestion="Try again")
        assert r["status"] == "error"
        assert r["suggestion"] == "Try again"

    def test_error_without_suggestion(self):
        r = error("Failed")
        assert "suggestion" not in r

    def test_paginated(self):
        r = paginated([{"id": 1}], total=50, offset=0, limit=10)
        assert r["count"] == 1
        assert r["total"] == 50

    def test_confirm_required(self):
        r = confirm_required("delete", "Database X")
        assert r["status"] == "confirmation_required"

    def test_format_duration_seconds(self):
        assert "s" in format_duration(5.5)

    def test_format_duration_minutes(self):
        assert "m" in format_duration(125)

    def test_format_duration_hours(self):
        assert "h" in format_duration(7200)


# ── Error Handling Tests ──────────────────────────────────────────

class TestErrors:
    def test_base_to_dict(self):
        e = OdooForgeError("Oops", suggestion="Fix it", code="TEST")
        d = e.to_dict()
        assert d["status"] == "error"
        assert d["code"] == "TEST"
        assert d["suggestion"] == "Fix it"

    def test_docker_not_running(self):
        e = DockerNotRunningError()
        d = e.to_dict()
        assert d["code"] == "DOCKER_NOT_RUNNING"
        assert "odoo_instance_start" in d["suggestion"]

    def test_enrich_access_denied(self):
        r = enrich_rpc_error("AccessDenied: wrong password")
        assert r["code"] == "AccessDenied"
        assert "credentials" in r["suggestion"]

    def test_enrich_unknown(self):
        r = enrich_rpc_error("Some weird error")
        assert r["code"] == "RPC_ERROR"
        assert "logs" in r["suggestion"]

    def test_enrich_validation_error(self):
        r = enrich_rpc_error("odoo.exceptions.ValidationError: missing name")
        assert r["code"] == "ValidationError"
