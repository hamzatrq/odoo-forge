"""Common validation logic for tool inputs."""

from __future__ import annotations

from typing import Any


def validate_domain(domain: list) -> list:
    """Validate and normalize an Odoo domain expression.

    Odoo domains are lists of tuples/lists like:
    [('field', 'operator', value), '|', ('field2', '=', value2)]
    """
    if not isinstance(domain, list):
        raise ValueError(f"Domain must be a list, got {type(domain).__name__}")

    valid_operators = {
        "=", "!=", ">", ">=", "<", "<=",
        "like", "ilike", "not like", "not ilike",
        "in", "not in",
        "=like", "=ilike",
        "child_of", "parent_of",
    }
    valid_connectors = {"&", "|", "!"}

    for item in domain:
        if isinstance(item, str):
            if item not in valid_connectors:
                raise ValueError(
                    f"Invalid domain connector '{item}'. "
                    f"Valid connectors: {valid_connectors}"
                )
        elif isinstance(item, (list, tuple)):
            if len(item) != 3:
                raise ValueError(
                    f"Domain tuple must have 3 elements (field, operator, value), "
                    f"got {len(item)}: {item}"
                )
            field, operator, value = item
            if not isinstance(field, str):
                raise ValueError(f"Field name must be a string, got: {field}")
            if operator not in valid_operators:
                raise ValueError(
                    f"Invalid operator '{operator}'. Valid: {valid_operators}"
                )
        else:
            raise ValueError(f"Invalid domain element: {item}")

    return domain


def validate_field_name(name: str) -> str:
    """Validate that a field name is syntactically valid."""
    if not name:
        raise ValueError("Field name cannot be empty")
    if not name.replace("_", "").replace(".", "").isalnum():
        raise ValueError(
            f"Invalid field name '{name}'. "
            "Field names should contain only letters, digits, underscores, and dots."
        )
    return name


def validate_model_name(model: str) -> str:
    """Validate that a model name follows Odoo conventions (dot-separated)."""
    if not model:
        raise ValueError("Model name cannot be empty")
    parts = model.split(".")
    if len(parts) < 2:
        raise ValueError(
            f"Model name '{model}' looks invalid. "
            "Odoo model names are dot-separated (e.g. 'res.partner', 'sale.order')."
        )
    return model


def validate_db_name(db_name: str) -> str:
    """Validate database name."""
    if not db_name:
        raise ValueError("Database name cannot be empty")
    if not db_name.replace("_", "").replace("-", "").isalnum():
        raise ValueError(
            f"Database name '{db_name}' contains invalid characters. "
            "Use only letters, digits, underscores, and hyphens."
        )
    return db_name
