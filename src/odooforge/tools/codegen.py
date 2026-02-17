"""Thin async wrapper for the code generation tool."""

from __future__ import annotations


async def odoo_generate_addon(
    module_name: str,
    models: list[dict],
    version: str = "18.0.1.0.0",
    author: str = "OdooForge",
    category: str = "Customizations",
    description: str = "",
    depends: list[str] | None = None,
    security_groups: list[dict] | None = None,
) -> dict:
    """Generate a complete installable Odoo 18 module as code."""
    from odooforge.codegen.addon_builder import build_addon

    return build_addon(
        module_name, models, version, author, category, description, depends, security_groups
    )
