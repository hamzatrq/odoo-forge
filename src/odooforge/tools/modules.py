"""Module management tools — list, info, install, upgrade, uninstall."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.docker_client import OdooDocker
from odooforge.connections.xmlrpc_client import OdooRPC
from odooforge.verification.state_cache import LiveStateCache
from odooforge.verification.verify_install import verify_module_installed

logger = logging.getLogger(__name__)


async def odoo_module_list_available(
    rpc: OdooRPC,
    db_name: str,
    category: str | None = None,
) -> dict[str, Any]:
    """List all modules available for installation.

    Args:
        category: Filter by module category (e.g., "Sales", "Inventory").
    """
    domain: list = []
    if category:
        domain.append(("category_id.name", "ilike", category))

    modules = rpc.search_read(
        "ir.module.module",
        domain,
        fields=["name", "shortdesc", "state", "category_id", "summary", "latest_version"],
        limit=200,
        order="name asc",
        db=db_name,
    )

    return {
        "modules": [
            {
                "name": m["name"],
                "title": m.get("shortdesc", ""),
                "state": m["state"],
                "category": m["category_id"][1] if isinstance(m.get("category_id"), (list, tuple)) else "",
                "summary": (m.get("summary") or "")[:100],
                "version": m.get("latest_version", ""),
            }
            for m in modules
        ],
        "count": len(modules),
    }


async def odoo_module_list_installed(
    rpc: OdooRPC,
    db_name: str,
) -> dict[str, Any]:
    """List all currently installed modules."""
    modules = rpc.search_read(
        "ir.module.module",
        [["state", "=", "installed"]],
        fields=["name", "shortdesc", "latest_version", "category_id"],
        limit=500,
        order="name asc",
        db=db_name,
    )

    return {
        "modules": [
            {
                "name": m["name"],
                "title": m.get("shortdesc", ""),
                "version": m.get("latest_version", ""),
                "category": m["category_id"][1] if isinstance(m.get("category_id"), (list, tuple)) else "",
            }
            for m in modules
        ],
        "count": len(modules),
    }


async def odoo_module_info(
    rpc: OdooRPC,
    db_name: str,
    module_name: str,
) -> dict[str, Any]:
    """Get detailed information about a specific module.

    Args:
        module_name: Technical name (e.g., "sale", "stock", "account").
    """
    modules = rpc.search_read(
        "ir.module.module",
        [["name", "=", module_name]],
        fields=[
            "name", "shortdesc", "state", "latest_version",
            "category_id", "summary", "description", "author",
            "website", "dependencies_id",
        ],
        limit=1,
        db=db_name,
    )

    if not modules:
        return {
            "found": False,
            "module_name": module_name,
            "message": (
                f"Module '{module_name}' not found. "
                "Check the technical name (e.g., 'sale' not 'Sales')."
            ),
        }

    m = modules[0]

    # Get dependency names
    deps = []
    if m.get("dependencies_id"):
        dep_records = rpc.read(
            "ir.module.module.dependency",
            m["dependencies_id"],
            fields=["name", "depend_id"],
            db=db_name,
        )
        deps = [d["name"] for d in dep_records]

    return {
        "found": True,
        "name": m["name"],
        "title": m.get("shortdesc", ""),
        "state": m["state"],
        "version": m.get("latest_version", ""),
        "category": m["category_id"][1] if isinstance(m.get("category_id"), (list, tuple)) else "",
        "summary": m.get("summary") or "",
        "author": m.get("author", ""),
        "website": m.get("website", ""),
        "dependencies": deps,
        "description": (m.get("description") or "")[:500],
    }


async def odoo_module_install(
    rpc: OdooRPC,
    docker: OdooDocker,
    cache: LiveStateCache,
    db_name: str,
    modules: list[str],
) -> dict[str, Any]:
    """Install one or more Odoo modules.

    Uses Odoo CLI for reliability. Dependencies are resolved automatically.
    Post-install verification checks module state and error logs.

    Args:
        modules: List of technical module names (e.g., ["sale", "stock"]).
    """
    if not modules:
        return {"status": "error", "message": "No modules specified."}

    # Check which are already installed
    already = []
    to_install = []
    for mod in modules:
        existing = rpc.search_read(
            "ir.module.module",
            [["name", "=", mod]],
            fields=["name", "state"],
            limit=1,
            db=db_name,
        )
        if existing and existing[0]["state"] == "installed":
            already.append(mod)
        else:
            to_install.append(mod)

    if not to_install:
        return {
            "status": "already_installed",
            "modules": already,
            "message": f"All requested modules are already installed: {already}",
        }

    # Install via CLI (more reliable for large modules)
    try:
        output = await docker.install_module_via_cli(db_name, to_install)
    except Exception as e:
        return {
            "status": "error",
            "modules": to_install,
            "message": f"Installation failed: {e}",
            "suggestion": "Create a snapshot before retrying. Check odoo_instance_logs for details.",
        }

    # Restart Odoo to ensure clean state
    await docker.restart_service("web")
    await docker.wait_for_healthy(timeout=120)

    # Re-authenticate
    rpc.uid = None
    rpc.authenticate(db_name)

    # Verify each module
    results = []
    for mod in to_install:
        verification = await verify_module_installed(rpc, docker, db_name, mod)
        results.append(verification)

    # Refresh cache
    cache.refresh_all()

    all_verified = all(r["verified"] for r in results)

    return {
        "status": "installed" if all_verified else "installed_with_issues",
        "installed": to_install,
        "already_installed": already,
        "verification": results,
        "message": (
            f"Installed {len(to_install)} module(s): {to_install}."
            + (f" Already installed: {already}." if already else "")
            + ("" if all_verified else " ⚠️ Some modules have verification issues — check 'verification' details.")
        ),
    }


async def odoo_module_upgrade(
    rpc: OdooRPC,
    docker: OdooDocker,
    cache: LiveStateCache,
    db_name: str,
    modules: list[str],
) -> dict[str, Any]:
    """Upgrade (update) installed modules to apply changes.

    Args:
        modules: List of module technical names to upgrade.
    """
    if not modules:
        return {"status": "error", "message": "No modules specified."}

    try:
        await docker.upgrade_module_via_cli(db_name, modules)
    except Exception as e:
        return {
            "status": "error",
            "modules": modules,
            "message": f"Upgrade failed: {e}",
        }

    # Restart and re-auth
    await docker.restart_service("web")
    await docker.wait_for_healthy(timeout=120)
    rpc.uid = None
    rpc.authenticate(db_name)
    cache.refresh_all()

    return {
        "status": "upgraded",
        "modules": modules,
        "message": f"Upgraded {len(modules)} module(s): {modules}. Odoo restarted.",
    }


async def odoo_module_uninstall(
    rpc: OdooRPC,
    docker: OdooDocker,
    cache: LiveStateCache,
    db_name: str,
    module_name: str,
    confirm: bool = False,
) -> dict[str, Any]:
    """Uninstall a module. This may remove data associated with the module.

    Args:
        module_name: Technical name of the module to uninstall.
        confirm: Must be true to proceed.
    """
    if not confirm:
        return {
            "status": "cancelled",
            "message": (
                f"Set confirm=true to uninstall '{module_name}'. "
                "⚠️ This may delete data created by the module. Create a snapshot first!"
            ),
        }

    # Use XML-RPC button_immediate_uninstall
    modules = rpc.search_read(
        "ir.module.module",
        [["name", "=", module_name]],
        fields=["id", "state"],
        limit=1,
        db=db_name,
    )

    if not modules:
        return {"status": "error", "message": f"Module '{module_name}' not found."}

    if modules[0]["state"] != "installed":
        return {"status": "error", "message": f"Module '{module_name}' is not installed (state: {modules[0]['state']})."}

    try:
        rpc.execute_method(
            "ir.module.module",
            "button_immediate_uninstall",
            args=[[modules[0]["id"]]],
            db=db_name,
        )
    except Exception as e:
        return {"status": "error", "message": f"Uninstall failed: {e}"}

    # Restart and refresh
    await docker.restart_service("web")
    await docker.wait_for_healthy(timeout=120)
    rpc.uid = None
    rpc.authenticate(db_name)
    cache.refresh_all()

    return {
        "status": "uninstalled",
        "module": module_name,
        "message": f"Module '{module_name}' uninstalled. Odoo restarted.",
    }
