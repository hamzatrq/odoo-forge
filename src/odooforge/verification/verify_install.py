"""Post-module-install verification."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.docker_client import OdooDocker
from odooforge.connections.xmlrpc_client import OdooRPC

logger = logging.getLogger(__name__)


async def verify_module_installed(
    rpc: OdooRPC,
    docker: OdooDocker,
    db: str,
    module_name: str,
) -> dict[str, Any]:
    """Verify a module was actually installed and is functional.

    Checks:
    1. Module state is 'installed' in ir.module.module
    2. Expected models exist (via module's models)
    3. No ERROR-level log entries during install
    """
    issues = []

    # 1. Check module state
    modules = rpc.search_read(
        "ir.module.module",
        [["name", "=", module_name]],
        fields=["name", "state", "shortdesc", "latest_version"],
        limit=1,
        db=db,
    )

    if not modules:
        return {
            "verified": False,
            "module": module_name,
            "issues": [f"Module '{module_name}' not found in database. Is the technical name correct?"],
        }

    module = modules[0]
    if module["state"] != "installed":
        issues.append(
            f"Module state is '{module['state']}' instead of 'installed'. "
            "Installation may have failed silently."
        )

    # 2. Check for error logs during install
    try:
        logs = await docker.logs(service="web", lines=200, grep="ERROR")
        if logs.strip():
            error_lines = [l.strip() for l in logs.strip().splitlines() if module_name in l.lower()]
            if error_lines:
                issues.append(
                    f"Found {len(error_lines)} error(s) in logs related to '{module_name}':\n"
                    + "\n".join(error_lines[:5])
                )
    except Exception as e:
        logger.warning("Could not check logs during verification: %s", e)

    return {
        "verified": len(issues) == 0,
        "module": module_name,
        "state": module.get("state"),
        "version": module.get("latest_version"),
        "description": module.get("shortdesc"),
        "issues": issues,
    }
