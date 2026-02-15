"""Tests for Phase 3 tools: views, reports, automation, network + utilities."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from odooforge.tools.views import (
    odoo_view_list, odoo_view_get_arch, odoo_view_modify,
    odoo_view_reset, odoo_view_list_customizations,
)
from odooforge.tools.reports import (
    odoo_report_list, odoo_report_get_template, odoo_report_modify,
    odoo_report_preview, odoo_report_reset, odoo_report_layout_configure,
)
from odooforge.tools.automation import (
    odoo_automation_list, odoo_automation_create, odoo_automation_update,
    odoo_automation_delete, odoo_email_template_create,
)
from odooforge.tools.network import (
    odoo_network_expose, odoo_network_status, odoo_network_stop,
    _active_tunnels,
)
from odooforge.utils.xpath_builder import (
    field_xpath, group_xpath, build_field_xml, build_inherit_xml,
)
from odooforge.utils.qweb_builder import (
    div_xpath, build_qweb_field, build_qweb_inherit_xml,
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
    m.execute.return_value = True
    return m


@pytest.fixture
def docker():
    m = MagicMock()
    m.restart_service = AsyncMock()
    return m


@pytest.fixture(autouse=True)
def clear_tunnels():
    _active_tunnels.clear()
    yield
    _active_tunnels.clear()


# ── XPath Builder Tests ───────────────────────────────────────────

class TestXPathBuilder:
    def test_field_xpath(self):
        assert field_xpath("email") == "//field[@name='email']"

    def test_group_xpath_by_name(self):
        assert group_xpath(name="details") == "//group[@name='details']"

    def test_group_xpath_by_string(self):
        assert group_xpath(string="Contact") == "//group[@string='Contact']"

    def test_build_field_xml(self):
        xml = build_field_xml("x_test", widget="monetary", string="Amount")
        assert 'name="x_test"' in xml
        assert 'widget="monetary"' in xml
        assert 'string="Amount"' in xml

    def test_build_field_xml_simple(self):
        xml = build_field_xml("name")
        assert xml == '<field name="name"/>'

    def test_build_inherit_xml(self):
        specs = [{"expr": "//field[@name='email']", "position": "after", "content": "<field name='x_test'/>"}]
        xml = build_inherit_xml(specs)
        assert "<data>" in xml
        assert "position=\"after\"" in xml
        assert "x_test" in xml


# ── QWeb Builder Tests ────────────────────────────────────────────

class TestQWebBuilder:
    def test_div_xpath(self):
        assert div_xpath("page") == "//div[hasclass('page')]"

    def test_build_qweb_field(self):
        xml = build_qweb_field("doc.name")
        assert 't-field="doc.name"' in xml

    def test_build_qweb_field_with_widget(self):
        xml = build_qweb_field("doc.amount", widget="monetary")
        assert "monetary" in xml

    def test_build_qweb_inherit_xml(self):
        specs = [{"expr": "//div", "position": "inside", "content": "<p>Hello</p>"}]
        xml = build_qweb_inherit_xml("sale.report", specs)
        assert "inherit_id" in xml
        assert "sale.report" in xml


# ── View Tools Tests ──────────────────────────────────────────────

class TestViewList:
    @pytest.mark.asyncio
    async def test_list_views(self, rpc):
        rpc.search_read.return_value = [
            {"id": 1, "name": "Partner Form", "model": "res.partner",
             "type": "form", "inherit_id": False, "priority": 16, "active": True},
        ]
        result = await odoo_view_list(rpc, "testdb")
        assert result["count"] == 1
        assert result["views"][0]["name"] == "Partner Form"


class TestViewGetArch:
    @pytest.mark.asyncio
    async def test_get_by_id(self, rpc):
        rpc.read.return_value = [{"id": 1, "name": "Form", "model": "res.partner",
                                   "type": "form", "arch": "<form/>"}]
        result = await odoo_view_get_arch(rpc, "testdb", view_id=1)
        assert result["found"] is True
        assert "<form/>" in result["arch"]

    @pytest.mark.asyncio
    async def test_no_params(self, rpc):
        result = await odoo_view_get_arch(rpc, "testdb")
        assert result["found"] is False


class TestViewModify:
    @pytest.mark.asyncio
    async def test_create_new(self, rpc, docker):
        rpc.read.return_value = [{"id": 1, "model": "res.partner", "type": "form", "name": "Partner"}]
        rpc.search_read.return_value = []  # no existing
        rpc.create.return_value = 42
        result = await odoo_view_modify(
            rpc, docker, "testdb", 1, "Custom Partner",
            [{"expr": "//field[@name='email']", "position": "after", "content": "<field name='x_test'/>"}],
        )
        assert result["status"] == "created"
        assert result["view_id"] == 42

    @pytest.mark.asyncio
    async def test_empty_specs(self, rpc, docker):
        result = await odoo_view_modify(rpc, docker, "testdb", 1, "Test", [])
        assert result["status"] == "error"


class TestViewReset:
    @pytest.mark.asyncio
    async def test_no_confirm(self, rpc):
        result = await odoo_view_reset(rpc, "testdb", 1)
        assert result["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_confirmed(self, rpc):
        rpc.read.return_value = [{"name": "Custom View", "inherit_id": [1, "Parent"]}]
        result = await odoo_view_reset(rpc, "testdb", 42, confirm=True)
        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_base_view(self, rpc):
        rpc.read.return_value = [{"name": "Base", "inherit_id": False}]
        result = await odoo_view_reset(rpc, "testdb", 1, confirm=True)
        assert result["status"] == "error"


class TestViewListCustomizations:
    @pytest.mark.asyncio
    async def test_list(self, rpc):
        rpc.search_read.return_value = [
            {"id": 10, "name": "Custom", "model": "res.partner", "type": "form",
             "inherit_id": [1, "Parent"], "priority": 99, "active": True},
        ]
        result = await odoo_view_list_customizations(rpc, "testdb")
        assert result["count"] == 1


# ── Report Tools Tests ────────────────────────────────────────────

class TestReportList:
    @pytest.mark.asyncio
    async def test_list_reports(self, rpc):
        rpc.search_read.return_value = [
            {"id": 1, "name": "Invoice", "model": "account.move",
             "report_name": "account.report_invoice", "report_type": "qweb-pdf",
             "binding_model_id": False},
        ]
        result = await odoo_report_list(rpc, "testdb")
        assert result["count"] == 1


class TestReportGetTemplate:
    @pytest.mark.asyncio
    async def test_found(self, rpc):
        rpc.search_read.side_effect = [
            [{"id": 1, "name": "Invoice", "model": "account.move", "report_name": "account.report_invoice"}],
            [{"id": 5, "name": "Invoice Template", "key": "account.report_invoice", "arch": "<t/>", "type": "qweb"}],
        ]
        result = await odoo_report_get_template(rpc, "testdb", "account.report_invoice")
        assert result["found"] is True
        assert len(result["templates"]) == 1

    @pytest.mark.asyncio
    async def test_not_found(self, rpc):
        result = await odoo_report_get_template(rpc, "testdb", "nope")
        assert result["found"] is False


class TestReportModify:
    @pytest.mark.asyncio
    async def test_create(self, rpc):
        rpc.read.return_value = [{"name": "Template", "key": "sale.report", "type": "qweb"}]
        rpc.search_read.return_value = []
        rpc.create.return_value = 99
        result = await odoo_report_modify(
            rpc, "testdb", 1,
            [{"expr": "//div", "position": "inside", "content": "<p>Added</p>"}],
        )
        assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_empty(self, rpc):
        result = await odoo_report_modify(rpc, "testdb", 1, [])
        assert result["status"] == "error"


class TestReportPreview:
    @pytest.mark.asyncio
    async def test_success(self, rpc):
        rpc.execute.return_value = ("<html>...</html>", "html")
        result = await odoo_report_preview(rpc, "testdb", "sale.report_saleorder", [1])
        assert result["status"] == "generated"

    @pytest.mark.asyncio
    async def test_no_ids(self, rpc):
        result = await odoo_report_preview(rpc, "testdb", "sale.report_saleorder", [])
        assert result["status"] == "error"


class TestReportReset:
    @pytest.mark.asyncio
    async def test_no_confirm(self, rpc):
        result = await odoo_report_reset(rpc, "testdb", 1)
        assert result["status"] == "cancelled"


class TestReportLayout:
    @pytest.mark.asyncio
    async def test_configure(self, rpc):
        rpc.search_read.side_effect = [
            [{"id": 1, "name": "A4"}],  # paperformat
            [{"id": 1}],  # company
        ]
        result = await odoo_report_layout_configure(rpc, "testdb", paperformat="A4")
        assert result["status"] == "configured"

    @pytest.mark.asyncio
    async def test_no_updates(self, rpc):
        result = await odoo_report_layout_configure(rpc, "testdb")
        assert result["status"] == "error"


# ── Automation Tools Tests ────────────────────────────────────────

class TestAutomationList:
    @pytest.mark.asyncio
    async def test_list(self, rpc):
        rpc.search_read.return_value = [
            {"id": 1, "name": "Auto Send", "model_id": [10, "res.partner"],
             "trigger": "on_create", "active": True, "action_server_ids": [1],
             "trigger_field_ids": [], "filter_domain": "[]", "last_run": False},
        ]
        result = await odoo_automation_list(rpc, "testdb")
        assert result["count"] == 1


class TestAutomationCreate:
    @pytest.mark.asyncio
    async def test_create(self, rpc):
        rpc.search_read.return_value = [{"id": 10}]  # model lookup
        rpc.create.side_effect = [100, 200]  # action, rule
        result = await odoo_automation_create(
            rpc, "testdb", "Test Rule", "res.partner", "on_create",
        )
        assert result["status"] == "created"
        assert result["rule_id"] == 200

    @pytest.mark.asyncio
    async def test_model_not_found(self, rpc):
        rpc.search_read.return_value = []
        result = await odoo_automation_create(
            rpc, "testdb", "Test", "bad.model", "on_create",
        )
        assert result["status"] == "error"


class TestAutomationUpdate:
    @pytest.mark.asyncio
    async def test_update(self, rpc):
        rpc.read.return_value = [{"name": "Rule"}]
        result = await odoo_automation_update(rpc, "testdb", 1, {"active": False})
        assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_not_found(self, rpc):
        result = await odoo_automation_update(rpc, "testdb", 999, {})
        assert result["status"] == "error"


class TestAutomationDelete:
    @pytest.mark.asyncio
    async def test_no_confirm(self, rpc):
        result = await odoo_automation_delete(rpc, "testdb", 1)
        assert result["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_confirmed(self, rpc):
        rpc.read.return_value = [{"name": "Rule"}]
        result = await odoo_automation_delete(rpc, "testdb", 1, confirm=True)
        assert result["status"] == "deleted"


class TestEmailTemplateCreate:
    @pytest.mark.asyncio
    async def test_create(self, rpc):
        rpc.search_read.return_value = [{"id": 10}]
        rpc.create.return_value = 50
        result = await odoo_email_template_create(
            rpc, "testdb", "Welcome", "res.partner",
            "Welcome {{ object.name }}", "<p>Hello!</p>",
        )
        assert result["status"] == "created"
        assert result["template_id"] == 50

    @pytest.mark.asyncio
    async def test_model_not_found(self, rpc):
        rpc.search_read.return_value = []
        result = await odoo_email_template_create(
            rpc, "testdb", "Test", "bad.model", "Subject", "<p>Body</p>",
        )
        assert result["status"] == "error"


# ── Network Tools Tests ───────────────────────────────────────────

class TestNetworkStatus:
    @pytest.mark.asyncio
    async def test_no_tunnels(self):
        result = await odoo_network_status()
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_with_tunnel(self):
        proc = MagicMock()
        proc.returncode = None
        proc.pid = 12345
        _active_tunnels["8069"] = proc
        result = await odoo_network_status()
        assert result["count"] == 1
        assert result["tunnels"][0]["pid"] == 12345


class TestNetworkStop:
    @pytest.mark.asyncio
    async def test_no_tunnel(self):
        result = await odoo_network_stop(port=8069)
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_stop_specific(self):
        proc = MagicMock()
        proc.returncode = None
        _active_tunnels["8069"] = proc
        result = await odoo_network_stop(port=8069)
        assert result["status"] == "stopped"
        proc.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_all(self):
        proc1, proc2 = MagicMock(), MagicMock()
        _active_tunnels["8069"] = proc1
        _active_tunnels["8070"] = proc2
        result = await odoo_network_stop()
        assert result["count"] == 2
        assert len(_active_tunnels) == 0


class TestNetworkExpose:
    @pytest.mark.asyncio
    async def test_already_running(self):
        proc = MagicMock()
        _active_tunnels["8069"] = proc
        result = await odoo_network_expose(port=8069)
        assert result["status"] == "already_running"

    @pytest.mark.asyncio
    async def test_unsupported_method(self):
        result = await odoo_network_expose(method="invalid")
        assert result["status"] == "error"
