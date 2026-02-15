"""Tests for LiveStateCache with mocked RPC."""

import pytest
from unittest.mock import MagicMock

from odooforge.verification.state_cache import LiveStateCache


@pytest.fixture
def rpc():
    return MagicMock()


@pytest.fixture
def cache(rpc):
    return LiveStateCache(rpc)


class TestRefresh:
    def test_not_initialized(self, cache):
        assert cache.is_initialized is False

    def test_refresh_modules(self, cache, rpc):
        rpc.search_read.return_value = [
            {"name": "base", "state": "installed", "shortdesc": "Base"},
            {"name": "sale", "state": "installed", "shortdesc": "Sales"},
        ]
        result = cache.refresh_modules()
        assert "base" in result
        assert "sale" in result
        assert cache.is_initialized is True

    def test_refresh_modules_error(self, cache, rpc):
        rpc.search_read.side_effect = Exception("connection lost")
        result = cache.refresh_modules()
        assert result == {}  # Returns empty, doesn't crash

    def test_refresh_model_fields(self, cache, rpc):
        rpc.fields_get.return_value = {
            "name": {"type": "char", "string": "Name"},
            "email": {"type": "char", "string": "Email"},
        }
        result = cache.refresh_model_fields("res.partner")
        assert "name" in result
        assert "email" in result

    def test_refresh_models(self, cache, rpc):
        rpc.search_read.return_value = [
            {"model": "res.partner"},
            {"model": "sale.order"},
        ]
        result = cache.refresh_models()
        assert "res.partner" in result
        assert "sale.order" in result


class TestQueries:
    def test_is_module_installed(self, cache, rpc):
        rpc.search_read.return_value = [
            {"name": "base", "state": "installed", "shortdesc": "Base"},
        ]
        cache.refresh_modules()
        assert cache.is_module_installed("base") is True
        assert cache.is_module_installed("sale") is False

    def test_is_field_valid_cached(self, cache, rpc):
        rpc.fields_get.return_value = {
            "name": {"type": "char"},
            "email": {"type": "char"},
        }
        cache.refresh_model_fields("res.partner")
        assert cache.is_field_valid("res.partner", "name") is True
        assert cache.is_field_valid("res.partner", "nonexistent") is False

    def test_is_field_valid_uncached_fetches(self, cache, rpc):
        rpc.fields_get.return_value = {"name": {"type": "char"}}
        # Not cached, should trigger a fetch
        result = cache.is_field_valid("sale.order", "name")
        assert result is True
        rpc.fields_get.assert_called_once()

    def test_validate_fields(self, cache, rpc):
        rpc.fields_get.return_value = {
            "name": {"type": "char"},
            "email": {"type": "char"},
        }
        cache.refresh_model_fields("res.partner")
        invalid = cache.validate_fields("res.partner", ["name", "bad_field", "email"])
        assert invalid == ["bad_field"]

    def test_validate_fields_id_always_valid(self, cache, rpc):
        rpc.fields_get.return_value = {"name": {"type": "char"}}
        cache.refresh_model_fields("res.partner")
        invalid = cache.validate_fields("res.partner", ["id", "name"])
        assert invalid == []

    def test_get_model_fields_none_if_uncached(self, cache):
        assert cache.get_model_fields("unknown.model") is None

    def test_get_installed_modules_returns_copy(self, cache, rpc):
        rpc.search_read.return_value = [
            {"name": "base", "state": "installed", "shortdesc": "Base"},
        ]
        cache.refresh_modules()
        modules = cache.get_installed_modules()
        modules["injected"] = "bad"
        # Original should not be mutated
        assert "injected" not in cache.get_installed_modules()
