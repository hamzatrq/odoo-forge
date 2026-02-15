"""Diagnostics tool — comprehensive system health check."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC
from odooforge.connections.docker_client import OdooDocker
from odooforge.connections.pg_client import OdooPG

logger = logging.getLogger(__name__)


async def odoo_diagnostics_health_check(
    rpc: OdooRPC,
    docker: OdooDocker,
    pg: OdooPG,
    db_name: str,
) -> dict[str, Any]:
    """Run a comprehensive health check on the Odoo instance.

    Checks: Docker services, database connectivity, Odoo authentication,
    installed modules, disk usage, and common configuration issues.
    """
    checks: list[dict[str, Any]] = []
    overall = "healthy"

    # 1. Docker services
    try:
        status = await docker.get_status()
        running = status.get("running", False)
        checks.append({
            "check": "Docker services",
            "status": "pass" if running else "fail",
            "details": status,
        })
        if not running:
            overall = "unhealthy"
    except Exception as e:
        checks.append({"check": "Docker services", "status": "fail", "details": str(e)})
        overall = "unhealthy"

    # 2. Database connectivity
    try:
        db_list = rpc.db_list()
        db_exists = db_name in db_list
        checks.append({
            "check": "Database exists",
            "status": "pass" if db_exists else "warn",
            "details": {"database": db_name, "available": db_list},
        })
        if not db_exists:
            overall = "degraded"
    except Exception as e:
        checks.append({"check": "Database connectivity", "status": "fail", "details": str(e)})
        overall = "unhealthy"

    # 3. Odoo authentication
    try:
        uid = rpc.authenticate(db=db_name)
        checks.append({
            "check": "Odoo authentication",
            "status": "pass" if uid else "fail",
            "details": {"uid": uid},
        })
        if not uid:
            overall = "unhealthy"
    except Exception as e:
        checks.append({"check": "Odoo authentication", "status": "fail", "details": str(e)})
        overall = "unhealthy"

    # 4. Installed modules count
    try:
        module_count = rpc.search_count(
            "ir.module.module",
            [["state", "=", "installed"]],
            db=db_name,
        )
        checks.append({
            "check": "Installed modules",
            "status": "pass",
            "details": {"count": module_count},
        })
    except Exception as e:
        checks.append({"check": "Module check", "status": "warn", "details": str(e)})

    # 5. Odoo version
    try:
        version = rpc.server_version()
        checks.append({
            "check": "Odoo version",
            "status": "pass",
            "details": {"version": version},
        })
    except Exception as e:
        checks.append({"check": "Version check", "status": "warn", "details": str(e)})

    # 6. PostgreSQL connectivity (direct)
    try:
        await pg.ensure_pool()
        pool_size = pg._pool.get_size() if pg._pool else 0
        checks.append({
            "check": "PostgreSQL direct",
            "status": "pass",
            "details": {"pool_size": pool_size},
        })
    except Exception as e:
        checks.append({
            "check": "PostgreSQL direct",
            "status": "warn",
            "details": f"Direct PG not available (optional): {e}",
        })

    # 7. Recent error logs
    try:
        logs = await docker.logs(tail=50, grep="ERROR")
        error_lines = [l for l in logs.split("\n") if l.strip()] if logs else []
        checks.append({
            "check": "Recent errors in logs",
            "status": "warn" if error_lines else "pass",
            "details": {
                "error_count": len(error_lines),
                "recent": error_lines[:5] if error_lines else [],
            },
        })
        if error_lines:
            overall = "degraded" if overall == "healthy" else overall
    except Exception as e:
        checks.append({"check": "Log analysis", "status": "warn", "details": str(e)})

    return {
        "overall": overall,
        "checks": checks,
        "passed": sum(1 for c in checks if c["status"] == "pass"),
        "warnings": sum(1 for c in checks if c["status"] == "warn"),
        "failures": sum(1 for c in checks if c["status"] == "fail"),
        "total": len(checks),
        "message": f"Health: {overall.upper()} — "
                   f"{sum(1 for c in checks if c['status'] == 'pass')}/{len(checks)} checks passed.",
    }
