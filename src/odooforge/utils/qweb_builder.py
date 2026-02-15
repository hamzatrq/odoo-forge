"""QWeb template builder utility for Odoo report customization.

Provides helpers for modifying QWeb report templates via XPath inheritance,
similar to how view inheritance works but for QWeb (PDF/HTML reports).
"""

from __future__ import annotations

from typing import Literal

Position = Literal["before", "after", "inside", "replace", "attributes"]


def qweb_xpath(expr: str, position: Position = "replace") -> dict:
    """Build a QWeb XPath spec for report modification."""
    return {"expr": expr, "position": position}


def div_xpath(css_class: str) -> str:
    """Target a div by CSS class in a QWeb template."""
    return f"//div[hasclass('{css_class}')]"


def span_xpath(css_class: str) -> str:
    """Target a span by CSS class."""
    return f"//span[hasclass('{css_class}')]"


def t_field_xpath(field_expr: str) -> str:
    """Target a t-field element by its expression."""
    return f"//span[@t-field='{field_expr}']"


def table_xpath(css_class: str = "table") -> str:
    """Target a table element."""
    return f"//table[hasclass('{css_class}')]"


def build_qweb_field(
    field_expr: str,
    widget: str | None = None,
    css_class: str | None = None,
    tag: str = "span",
) -> str:
    """Generate a QWeb field element.

    Args:
        field_expr: Odoo field expression (e.g., "doc.partner_id.name").
        widget: Optional QWeb widget (e.g., "monetary", "date").
        css_class: Optional CSS class.
        tag: HTML tag to use (default: span).
    """
    attrs = [f't-field="{field_expr}"']
    if widget:
        attrs.append(f't-options=\'{{"widget": "{widget}"}}\'')
    if css_class:
        attrs.append(f'class="{css_class}"')

    return f"<{tag} {' '.join(attrs)}/>"


def build_qweb_inherit_xml(
    template_id: str,
    xpath_specs: list[dict],
) -> str:
    """Build a complete QWeb template inheritance XML.

    Args:
        template_id: ID of the template to inherit from.
        xpath_specs: List of XPath modifications.
            Each: {"expr": "...", "position": "...", "content": "..."}
    """
    parts = [
        f'<template id="{template_id}_custom" inherit_id="{template_id}">',
    ]
    for spec in xpath_specs:
        expr = spec["expr"]
        pos = spec.get("position", "replace")
        content = spec.get("content", "")
        parts.append(f'  <xpath expr="{expr}" position="{pos}">')
        if content:
            parts.append(f"    {content}")
        parts.append("  </xpath>")
    parts.append("</template>")
    return "\n".join(parts)


def build_style_block(css: str) -> str:
    """Wrap CSS in a style tag for QWeb reports."""
    return f"<style>{css}</style>"


def build_header_footer(
    content: str,
    section: str = "header",
) -> str:
    """Generate header or footer HTML for reports.

    Args:
        content: HTML content for the header/footer.
        section: 'header' or 'footer'.
    """
    return f'<div class="header" t-if="section == \'{section}\'">{content}</div>'
