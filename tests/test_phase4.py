"""Tests for Phase 4 tools: imports, email, settings, knowledge, diagnostics."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from odooforge.tools.imports import (
    odoo_import_preview, odoo_import_execute, odoo_import_template,
)
from odooforge.tools.email import (
    odoo_email_configure_outgoing, odoo_email_configure_incoming,
    odoo_email_test, odoo_email_dns_guide,
)
from odooforge.tools.settings import (
    odoo_settings_get, odoo_settings_set, odoo_company_configure, odoo_users_manage,
)
from odooforge.tools.knowledge import (
    odoo_knowledge_module_info, odoo_knowledge_search, odoo_knowledge_community_gaps,
)
from odooforge.utils.binary_handler import (
    encode_file, csv_to_import_data, format_file_size,
)


# ── Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def rpc():
    m = MagicMock()
    m.search_read.return_value = []
    m.read.return_value = []
    m.create.return_value = 1
    m.write.return_value = True
    m.unlink.return_value = True
    m.fields_get.return_value = {
        "name": {"string": "Name", "type": "char", "required": True, "readonly": False},
        "email": {"string": "Email", "type": "char", "required": False, "readonly": False},
    }
    m.load.return_value = {"ids": [1, 2, 3], "messages": []}
    m.execute_method.return_value = True
    m.search_count.return_value = 5
    m.db_list.return_value = ["testdb"]
    m.authenticate.return_value = 2
    m.server_version.return_value = "18.0"
    return m


# ── Binary Handler Tests ──────────────────────────────────────────

class TestBinaryHandler:
    def test_encode_missing_file(self):
        result = encode_file("/nonexistent/file.txt")
        assert "error" in result

    def test_csv_to_import_data(self):
        result = csv_to_import_data("name,email\nAlice,a@b.com\nBob,b@c.com")
        assert result["headers"] == ["name", "email"]
        assert result["row_count"] == 2

    def test_csv_empty(self):
        result = csv_to_import_data("")
        assert "error" in result

    def test_format_file_size(self):
        assert "KB" in format_file_size(2048)
        assert "MB" in format_file_size(2 * 1024 * 1024)
        assert "B" in format_file_size(100)


# ── Import Tests ──────────────────────────────────────────────────

class TestImportPreview:
    @pytest.mark.asyncio
    async def test_preview(self, rpc):
        csv = "name,email\nAlice,a@b.com"
        result = await odoo_import_preview(rpc, "testdb", "res.partner", csv)
        assert result["status"] == "preview"
        assert result["total_rows"] == 1
        assert result["valid_fields"] == 2

    @pytest.mark.asyncio
    async def test_preview_invalid_field(self, rpc):
        csv = "name,bad_field\nAlice,value"
        result = await odoo_import_preview(rpc, "testdb", "res.partner", csv)
        assert result["invalid_fields"] == 1

    @pytest.mark.asyncio
    async def test_preview_empty(self, rpc):
        result = await odoo_import_preview(rpc, "testdb", "res.partner", "")
        assert result["status"] == "error"


class TestImportExecute:
    @pytest.mark.asyncio
    async def test_execute(self, rpc):
        csv = "name,email\nAlice,a@b.com\nBob,b@c.com\nCharlie,c@d.com"
        result = await odoo_import_execute(rpc, "testdb", "res.partner", csv)
        assert result["status"] == "imported"
        assert result["imported"] == 3


class TestImportTemplate:
    @pytest.mark.asyncio
    async def test_template(self, rpc):
        result = await odoo_import_template(rpc, "testdb", "res.partner")
        assert result["field_count"] >= 1
        assert "csv_header" in result


# ── Email Tests ───────────────────────────────────────────────────

class TestEmailOutgoing:
    @pytest.mark.asyncio
    async def test_create(self, rpc):
        rpc.create.return_value = 10
        result = await odoo_email_configure_outgoing(
            rpc, "testdb", "Gmail", "smtp.gmail.com",
        )
        assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_update_existing(self, rpc):
        rpc.search_read.return_value = [{"id": 5}]
        result = await odoo_email_configure_outgoing(
            rpc, "testdb", "Gmail", "smtp.gmail.com",
        )
        assert result["status"] == "updated"


class TestEmailIncoming:
    @pytest.mark.asyncio
    async def test_create(self, rpc):
        rpc.create.return_value = 10
        result = await odoo_email_configure_incoming(
            rpc, "testdb", "Inbox", host="imap.gmail.com",
        )
        assert result["status"] == "created"


class TestEmailTest:
    @pytest.mark.asyncio
    async def test_send(self, rpc):
        rpc.create.return_value = 100
        result = await odoo_email_test(rpc, "testdb", "test@example.com")
        assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_failure(self, rpc):
        rpc.create.side_effect = Exception("SMTP error")
        result = await odoo_email_test(rpc, "testdb", "test@example.com")
        assert result["status"] == "error"


class TestDnsGuide:
    @pytest.mark.asyncio
    async def test_generate(self):
        result = await odoo_email_dns_guide("example.com")
        assert result["domain"] == "example.com"
        assert len(result["records"]) == 4


# ── Settings Tests ────────────────────────────────────────────────

class TestSettingsGet:
    @pytest.mark.asyncio
    async def test_get(self, rpc):
        rpc.create.return_value = 1
        rpc.read.return_value = [{"id": 1, "module_sale": True}]
        result = await odoo_settings_get(rpc, "testdb")
        assert result["status"] == "ok"


class TestSettingsSet:
    @pytest.mark.asyncio
    async def test_set(self, rpc):
        rpc.create.return_value = 1
        result = await odoo_settings_set(rpc, "testdb", {"module_sale": True})
        assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_set_empty(self, rpc):
        result = await odoo_settings_set(rpc, "testdb", {})
        assert result["status"] == "error"


class TestCompanyConfigure:
    @pytest.mark.asyncio
    async def test_configure(self, rpc):
        rpc.search_read.return_value = [{"id": 1, "name": "My Company"}]
        result = await odoo_company_configure(rpc, "testdb", {"name": "New Name"})
        assert result["status"] == "configured"

    @pytest.mark.asyncio
    async def test_no_updates(self, rpc):
        result = await odoo_company_configure(rpc, "testdb", {})
        assert result["status"] == "error"


class TestUsersManage:
    @pytest.mark.asyncio
    async def test_list(self, rpc):
        rpc.search_read.return_value = [
            {"id": 2, "name": "Admin", "login": "admin", "email": "a@b.com",
             "active": True, "groups_id": [1]},
        ]
        result = await odoo_users_manage(rpc, "testdb", action="list")
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_create(self, rpc):
        rpc.create.return_value = 10
        result = await odoo_users_manage(
            rpc, "testdb", action="create",
            values={"name": "Test", "login": "test"},
        )
        assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_create_missing_fields(self, rpc):
        result = await odoo_users_manage(rpc, "testdb", action="create", values={})
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_deactivate(self, rpc):
        result = await odoo_users_manage(rpc, "testdb", action="deactivate", user_id=5)
        assert result["status"] == "deactivated"

    @pytest.mark.asyncio
    async def test_invalid_action(self, rpc):
        result = await odoo_users_manage(rpc, "testdb", action="invalid")
        assert result["status"] == "error"


# ── Knowledge Tests ───────────────────────────────────────────────

class TestKnowledgeModuleInfo:
    @pytest.mark.asyncio
    async def test_known_module(self):
        result = await odoo_knowledge_module_info("sale")
        assert result["found"] is True
        assert "sales" in result["name"].lower()

    @pytest.mark.asyncio
    async def test_unknown_module(self):
        result = await odoo_knowledge_module_info("nonexistent_module")
        assert result["found"] is False


class TestKnowledgeSearch:
    @pytest.mark.asyncio
    async def test_search_invoice(self):
        result = await odoo_knowledge_search("accounting")
        assert result["count"] > 0

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        result = await odoo_knowledge_search("xyznonexistent123")
        assert result["count"] == 0


class TestKnowledgeCommunityGaps:
    @pytest.mark.asyncio
    async def test_with_gaps(self, rpc):
        rpc.search_read.side_effect = [
            [{"name": "sale"}, {"name": "account"}],  # installed modules
            [{"id": 1, "name": "My Co", "currency_id": [1, "USD"],
              "country_id": False, "email": ""}],  # company
        ]
        result = await odoo_knowledge_community_gaps(rpc, "testdb")
        assert result["count"] > 0  # Should suggest CRM and company config

    @pytest.mark.asyncio
    async def test_no_gaps(self, rpc):
        rpc.search_read.side_effect = [
            [{"name": "sale"}, {"name": "crm"}, {"name": "purchase"},
             {"name": "account"}, {"name": "stock"}, {"name": "hr"},
             {"name": "hr_holidays"}, {"name": "website"}, {"name": "website_sale"}],
            [{"id": 1, "name": "My Co", "currency_id": [1, "USD"],
              "country_id": [1, "US"], "email": "info@example.com"}],
        ]
        result = await odoo_knowledge_community_gaps(rpc, "testdb")
        assert result["count"] == 0
