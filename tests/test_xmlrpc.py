"""Tests for XML-RPC client with mocked xmlrpc.client."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import xmlrpc.client

from odooforge.connections.xmlrpc_client import OdooRPC, OdooRPCError


@pytest.fixture
def rpc():
    """Create an OdooRPC instance with mocked proxies."""
    with patch("xmlrpc.client.ServerProxy") as mock_proxy:
        client = OdooRPC(url="http://localhost:8069", db="testdb", username="admin", password="admin")
        # Replace internals with mocks
        client._common = MagicMock()
        client._object = MagicMock()
        return client


class TestAuthentication:
    def test_authenticate_success(self, rpc):
        rpc._common.authenticate.return_value = 2
        uid = rpc.authenticate("testdb")
        assert uid == 2
        assert rpc.uid == 2

    def test_authenticate_failure(self, rpc):
        rpc._common.authenticate.return_value = False
        with pytest.raises(OdooRPCError, match="Authentication failed"):
            rpc.authenticate("testdb")

    def test_authenticate_no_db(self, rpc):
        rpc.db = ""
        with pytest.raises(OdooRPCError, match="No database specified"):
            rpc.authenticate()

    def test_authenticate_connection_error(self, rpc):
        rpc._common.authenticate.side_effect = ConnectionError("refused")
        with pytest.raises(OdooRPCError, match="Cannot connect"):
            rpc.authenticate("testdb")

    def test_authenticate_fault(self, rpc):
        rpc._common.authenticate.side_effect = xmlrpc.client.Fault(1, "bad")
        with pytest.raises(OdooRPCError, match="fault"):
            rpc.authenticate("testdb")


class TestExecute:
    def test_execute_success(self, rpc):
        rpc._common.authenticate.return_value = 2
        rpc._object.execute_kw.return_value = [{"id": 1, "name": "Test"}]
        result = rpc.execute("res.partner", "search_read", [])
        assert result == [{"id": 1, "name": "Test"}]

    def test_execute_fault(self, rpc):
        rpc._common.authenticate.return_value = 2
        rpc._object.execute_kw.side_effect = xmlrpc.client.Fault(2, "Access Denied")
        with pytest.raises(OdooRPCError, match="Access Denied"):
            rpc.execute("res.partner", "search_read", [])

    def test_execute_retry_on_connection_error(self, rpc):
        rpc._common.authenticate.return_value = 2
        # Fail twice, succeed on third
        rpc._object.execute_kw.side_effect = [
            ConnectionError("lost"),
            ConnectionError("lost again"),
            [{"id": 1}],
        ]
        result = rpc.execute("res.partner", "search_read", [], max_retries=3)
        assert result == [{"id": 1}]
        assert rpc._object.execute_kw.call_count == 3

    def test_execute_exhausted_retries(self, rpc):
        rpc._common.authenticate.return_value = 2
        rpc._object.execute_kw.side_effect = ConnectionError("down")
        with pytest.raises(OdooRPCError, match="Failed after 2 attempts"):
            rpc.execute("res.partner", "read", [], max_retries=2)


class TestConvenienceMethods:
    def test_search_read(self, rpc):
        rpc._common.authenticate.return_value = 2
        rpc._object.execute_kw.return_value = [{"id": 1}]
        result = rpc.search_read("res.partner", [("name", "=", "Test")], fields=["name"], limit=5)
        assert result == [{"id": 1}]
        # Verify execute_kw was called with proper args
        call_args = rpc._object.execute_kw.call_args
        # execute_kw(db, uid, password, model, method, args, kwargs)
        assert call_args[0][3] == "res.partner"  # model
        assert call_args[0][4] == "search_read"  # method

    def test_create(self, rpc):
        rpc._common.authenticate.return_value = 2
        rpc._object.execute_kw.return_value = 42
        result = rpc.create("res.partner", {"name": "New"})
        assert result == 42

    def test_write(self, rpc):
        rpc._common.authenticate.return_value = 2
        rpc._object.execute_kw.return_value = True
        result = rpc.write("res.partner", [1], {"name": "Updated"})
        assert result is True

    def test_unlink(self, rpc):
        rpc._common.authenticate.return_value = 2
        rpc._object.execute_kw.return_value = True
        result = rpc.unlink("res.partner", [1])
        assert result is True

    def test_fields_get(self, rpc):
        rpc._common.authenticate.return_value = 2
        rpc._object.execute_kw.return_value = {
            "name": {"type": "char", "string": "Name"},
            "email": {"type": "char", "string": "Email"},
        }
        result = rpc.fields_get("res.partner")
        assert "name" in result
        assert "email" in result

    def test_search_count(self, rpc):
        rpc._common.authenticate.return_value = 2
        rpc._object.execute_kw.return_value = 15
        result = rpc.search_count("res.partner", [])
        assert result == 15

    def test_load(self, rpc):
        rpc._common.authenticate.return_value = 2
        rpc._object.execute_kw.return_value = {"ids": [1, 2], "messages": []}
        result = rpc.load("res.partner", ["name"], [["Alice"], ["Bob"]])
        assert result["ids"] == [1, 2]


class TestDatabaseMethods:
    def test_db_list(self, rpc):
        mock_db = MagicMock()
        mock_db.list.return_value = ["db1", "db2"]
        with patch.object(rpc, "_db_proxy", return_value=mock_db):
            result = rpc.db_list()
            assert result == ["db1", "db2"]

    def test_db_exists(self, rpc):
        mock_db = MagicMock()
        mock_db.list.return_value = ["mydb"]
        with patch.object(rpc, "_db_proxy", return_value=mock_db):
            assert rpc.db_exists("mydb") is True
            assert rpc.db_exists("other") is False

    def test_db_create(self, rpc):
        mock_db = MagicMock()
        mock_db.create_database.return_value = True
        with patch.object(rpc, "_db_proxy", return_value=mock_db):
            result = rpc.db_create("admin", "newdb")
            assert result is True

    def test_db_drop(self, rpc):
        mock_db = MagicMock()
        mock_db.drop.return_value = True
        with patch.object(rpc, "_db_proxy", return_value=mock_db):
            result = rpc.db_drop("admin", "olddb")
            assert result is True

    def test_server_version(self, rpc):
        rpc._common.version.return_value = {"server_version": "18.0"}
        assert rpc.server_version() == "18.0"
