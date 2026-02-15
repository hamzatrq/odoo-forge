"""Tests for config module."""

import os
import pytest
from odooforge.config import OdooForgeConfig, get_config, reset_config


class TestConfig:
    def setup_method(self):
        reset_config()

    def test_defaults(self):
        cfg = OdooForgeConfig()
        assert cfg.odoo_url == "http://localhost:8069"
        assert cfg.odoo_master_password == "admin"
        assert cfg.postgres_port == 5432
        assert cfg.postgres_user == "odoo"

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("ODOO_URL", "http://custom:9090")
        monkeypatch.setenv("POSTGRES_PORT", "5433")
        monkeypatch.setenv("ODOO_DEFAULT_DB", "testdb")
        cfg = OdooForgeConfig.from_env()
        assert cfg.odoo_url == "http://custom:9090"
        assert cfg.postgres_port == 5433
        assert cfg.odoo_default_db == "testdb"

    def test_frozen(self):
        cfg = OdooForgeConfig()
        with pytest.raises(AttributeError):
            cfg.odoo_url = "http://other"

    def test_singleton(self):
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2

    def test_reset(self):
        c1 = get_config()
        reset_config()
        c2 = get_config()
        # After reset, a new instance is created (might be equal but not same object)
        assert c1 is not c2
