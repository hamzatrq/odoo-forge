"""Generate __manifest__.py content for an Odoo addon."""

from __future__ import annotations


def generate_manifest(
    module_name: str,
    version: str,
    author: str,
    category: str,
    description: str,
    depends: list[str],
    has_views: bool = True,
    has_security: bool = True,
    models: list[dict] | None = None,
    security_groups: list[dict] | None = None,
) -> str:
    """Generate __manifest__.py content."""
    data_files: list[str] = []

    if has_security:
        data_files.append("security/ir.model.access.csv")
        if security_groups:
            data_files.append(f"security/{module_name}_security.xml")

    if has_views and models:
        for model in models:
            model_technical = model["name"].replace(".", "_")
            data_files.append(f"views/{model_technical}_views.xml")

    manifest = {
        "name": description or module_name,
        "version": version,
        "author": author,
        "category": category,
        "summary": description or f"Custom module: {module_name}",
        "depends": depends,
        "data": data_files,
        "installable": True,
        "application": False,
        "license": "LGPL-3",
    }

    lines = ["{\n"]
    for key, value in manifest.items():
        lines.append(f"    {key!r}: {value!r},\n")
    lines.append("}\n")
    return "".join(lines)
