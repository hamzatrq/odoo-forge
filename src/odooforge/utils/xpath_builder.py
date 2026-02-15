"""XPath builder utility for Odoo view inheritance.

Generates correct XPath expressions for modifying Odoo views
(form, tree, kanban, search) using the ir.ui.view inheritance mechanism.
"""

from __future__ import annotations

from typing import Literal

Position = Literal["before", "after", "inside", "replace", "attributes"]


def xpath_node(
    expr: str,
    position: Position = "inside",
) -> dict:
    """Build an XPath spec dict for view modification.

    Args:
        expr: XPath expression (e.g., "//field[@name='email']").
        position: Where to place the new content relative to the match.
    """
    return {"expr": expr, "position": position}


def field_xpath(field_name: str, position: Position = "after") -> str:
    """Build an XPath expression targeting a field by name."""
    return f"//field[@name='{field_name}']"


def group_xpath(name: str | None = None, string: str | None = None) -> str:
    """Build an XPath expression targeting a group element."""
    if name:
        return f"//group[@name='{name}']"
    if string:
        return f"//group[@string='{string}']"
    return "//group"


def page_xpath(name: str | None = None, string: str | None = None) -> str:
    """Build an XPath for a notebook page."""
    if name:
        return f"//page[@name='{name}']"
    if string:
        return f"//page[@string='{string}']"
    return "//page"


def button_xpath(name: str) -> str:
    """Build an XPath for a button by name."""
    return f"//button[@name='{name}']"


def header_xpath() -> str:
    """XPath for the form header (status bar area)."""
    return "//header"


def sheet_xpath() -> str:
    """XPath for the form sheet (main content area)."""
    return "//sheet"


def notebook_xpath() -> str:
    """XPath for the notebook element."""
    return "//notebook"


def build_field_xml(
    field_name: str,
    widget: str | None = None,
    string: str | None = None,
    invisible: str | None = None,
    readonly: str | None = None,
    required: str | None = None,
    options: str | None = None,
) -> str:
    """Generate XML for a field element with optional attributes.

    Returns a string like: <field name="x_custom" widget="monetary"/>
    """
    attrs = [f'name="{field_name}"']
    if widget:
        attrs.append(f'widget="{widget}"')
    if string:
        attrs.append(f'string="{string}"')
    if invisible:
        attrs.append(f'invisible="{invisible}"')
    if readonly:
        attrs.append(f'readonly="{readonly}"')
    if required:
        attrs.append(f'required="{required}"')
    if options:
        attrs.append(f'options="{options}"')

    return f"<field {' '.join(attrs)}/>"


def build_page_xml(
    name: str,
    string: str,
    content: str = "",
) -> str:
    """Generate XML for a notebook page."""
    return f'<page name="{name}" string="{string}"><group>{content}</group></page>'


def build_inherit_xml(
    xpath_specs: list[dict],
) -> str:
    """Build a complete inheritance arch XML from a list of XPath specs.

    Each spec: {"expr": "//field[@name='x']", "position": "after", "content": "<field .../>"}
    """
    parts = ['<data>']
    for spec in xpath_specs:
        expr = spec["expr"]
        pos = spec.get("position", "inside")
        content = spec.get("content", "")
        parts.append(f'  <xpath expr="{expr}" position="{pos}">')
        if content:
            parts.append(f"    {content}")
        parts.append("  </xpath>")
    parts.append("</data>")
    return "\n".join(parts)
