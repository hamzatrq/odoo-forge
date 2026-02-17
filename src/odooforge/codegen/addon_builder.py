"""Orchestrate all generators to produce a complete Odoo 18 addon module."""

from __future__ import annotations


def build_addon(
    module_name: str,
    models: list[dict],
    version: str = "18.0.1.0.0",
    author: str = "OdooForge",
    category: str = "Customizations",
    description: str = "",
    depends: list[str] | None = None,
    security_groups: list[dict] | None = None,
) -> dict:
    """Orchestrate all generators to produce a complete Odoo module.

    Returns a dict with module_name, files (path -> content), and summary.
    """
    from odooforge.codegen.manifest_gen import generate_manifest
    from odooforge.codegen.model_gen import (
        generate_models,
        generate_models_init,
        generate_top_init,
    )
    from odooforge.codegen.security_gen import generate_access_csv, generate_security_xml
    from odooforge.codegen.view_gen import generate_views

    # Auto-detect depends from model mixins
    if depends is None:
        depends = ["base"]
        for model in models:
            for inherit in model.get("inherit", []):
                if inherit in ("mail.thread", "mail.activity.mixin"):
                    if "mail" not in depends:
                        depends.append("mail")

    files: dict[str, str] = {}

    # Models
    for model in models:
        model_technical = model["name"].replace(".", "_")
        files[f"models/{model_technical}.py"] = generate_models(model)
    files["models/__init__.py"] = generate_models_init(models)
    files["__init__.py"] = generate_top_init()

    # Views
    for model in models:
        model_technical = model["name"].replace(".", "_")
        files[f"views/{model_technical}_views.xml"] = generate_views(model)

    # Security
    files["security/ir.model.access.csv"] = generate_access_csv(models, security_groups)
    if security_groups:
        files[f"security/{module_name}_security.xml"] = generate_security_xml(
            module_name, security_groups
        )

    # Manifest (last, so it knows all files)
    files["__manifest__.py"] = generate_manifest(
        module_name=module_name,
        version=version,
        author=author,
        category=category,
        description=description,
        depends=depends,
        has_views=True,
        has_security=True,
        models=models,
        security_groups=security_groups,
    )

    return {
        "module_name": module_name,
        "files": files,
        "summary": {
            "total_files": len(files),
            "models": len(models),
            "fields": sum(len(m.get("fields", [])) for m in models),
            "views": len(models) * 3,  # form + tree + search per model
            "security_groups": len(security_groups) if security_groups else 0,
        },
    }
