"""Tests for utility modules: validators, formatting, errors."""

import pytest

from odooforge.utils.validators import (
    validate_db_name,
    validate_domain,
    validate_field_name,
    validate_model_name,
)
from odooforge.utils.formatting import format_table, format_record, format_records, truncate
from odooforge.utils.errors import OdooForgeError, DockerNotRunningError


# ── Domain validation ───────────────────────────────────────────────

class TestValidateDomain:
    def test_empty_domain(self):
        assert validate_domain([]) == []

    def test_valid_simple_domain(self):
        domain = [("name", "=", "Test")]
        assert validate_domain(domain) == domain

    def test_valid_complex_domain(self):
        domain = ["|", ("name", "ilike", "test"), ("email", "!=", False)]
        assert validate_domain(domain) == domain

    def test_valid_in_operator(self):
        domain = [("id", "in", [1, 2, 3])]
        assert validate_domain(domain) == domain

    def test_invalid_operator(self):
        with pytest.raises(ValueError, match="Invalid operator"):
            validate_domain([("name", "EQUALS", "test")])

    def test_invalid_connector(self):
        with pytest.raises(ValueError, match="Invalid domain connector"):
            validate_domain(["AND", ("name", "=", "test")])

    def test_invalid_tuple_length(self):
        with pytest.raises(ValueError, match="3 elements"):
            validate_domain([("name", "=")])

    def test_not_a_list(self):
        with pytest.raises(ValueError, match="must be a list"):
            validate_domain("bad")

    def test_invalid_element_type(self):
        with pytest.raises(ValueError, match="Invalid domain element"):
            validate_domain([42])

    def test_all_operators(self):
        operators = ["=", "!=", ">", ">=", "<", "<=", "like", "ilike",
                     "not like", "not ilike", "in", "not in",
                     "=like", "=ilike", "child_of", "parent_of"]
        for op in operators:
            domain = [("field", op, "val")]
            assert validate_domain(domain) == domain


# ── Field name validation ───────────────────────────────────────────

class TestValidateFieldName:
    def test_valid_names(self):
        assert validate_field_name("name") == "name"
        assert validate_field_name("partner_id") == "partner_id"
        assert validate_field_name("x_custom.field") == "x_custom.field"

    def test_empty_name(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_field_name("")

    def test_invalid_characters(self):
        with pytest.raises(ValueError, match="Invalid field name"):
            validate_field_name("name with spaces")


# ── Model name validation ──────────────────────────────────────────

class TestValidateModelName:
    def test_valid_models(self):
        assert validate_model_name("res.partner") == "res.partner"
        assert validate_model_name("sale.order.line") == "sale.order.line"

    def test_single_segment(self):
        with pytest.raises(ValueError, match="dot-separated"):
            validate_model_name("partner")

    def test_empty(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_model_name("")


# ── DB name validation ─────────────────────────────────────────────

class TestValidateDbName:
    def test_valid_names(self):
        assert validate_db_name("mydb") == "mydb"
        assert validate_db_name("my-db_01") == "my-db_01"

    def test_empty(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_db_name("")

    def test_invalid_characters(self):
        with pytest.raises(ValueError, match="invalid characters"):
            validate_db_name("my db!")


# ── Formatting ──────────────────────────────────────────────────────

class TestFormatTable:
    def test_basic_table(self):
        result = format_table(["Name", "Age"], [["Alice", "30"], ["Bob", "25"]])
        assert "| Name" in result
        assert "Alice" in result
        assert "Bob" in result
        assert "---" in result

    def test_empty_rows(self):
        assert format_table(["Col"], []) == "_No data_"


class TestFormatRecord:
    def test_basic_record(self):
        result = format_record({"name": "Test", "email": "t@t.com"}, title="Partner")
        assert "### Partner" in result
        assert "**name**" in result
        assert "t@t.com" in result

    def test_no_title(self):
        result = format_record({"x": 1})
        assert "###" not in result


class TestFormatRecords:
    def test_empty_records(self):
        result = format_records([], title="Items")
        assert "No records found" in result

    def test_pagination_message(self):
        records = [{"id": i} for i in range(30)]
        result = format_records(records, limit=10)
        assert "Showing 10 of 30" in result


class TestTruncate:
    def test_short_text(self):
        assert truncate("hello", 100) == "hello"

    def test_long_text(self):
        result = truncate("a" * 3000, 2000)
        assert "truncated" in result
        assert len(result) < 3000


# ── Error classes ───────────────────────────────────────────────────

class TestErrors:
    def test_base_error_with_suggestion(self):
        err = OdooForgeError("Something broke", suggestion="Try restarting")
        assert "Something broke" in str(err)
        assert "Try restarting" in str(err)

    def test_base_error_no_suggestion(self):
        err = OdooForgeError("Simple error")
        assert "Suggestion" not in str(err)

    def test_docker_not_running(self):
        err = DockerNotRunningError()
        assert "not running" in str(err)
        assert "odoo_instance_start" in str(err)
