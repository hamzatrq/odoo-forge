"""Instance management tools — start, stop, restart, status, logs."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from odooforge.connections.docker_client import OdooDocker
from odooforge.connections.xmlrpc_client import OdooRPC

logger = logging.getLogger(__name__)


async def odoo_instance_start(
    docker: OdooDocker,
    rpc: OdooRPC,
    port: int = 8069,
) -> dict[str, Any]:
    """Start the Odoo Docker environment (Odoo + PostgreSQL).

    Brings up both containers and waits for Odoo to be healthy.
    """
    result = await docker.up(detach=True)

    # Wait for Odoo to be accessible
    await docker.wait_for_healthy(timeout=120)

    # Get version info
    try:
        version = rpc.server_version()
    except Exception:
        version = "unknown"

    return {
        "status": "running",
        "url": f"http://localhost:{port}",
        "odoo_version": version,
        "message": f"Odoo is running at http://localhost:{port}",
    }


async def odoo_instance_stop(
    docker: OdooDocker,
    remove_volumes: bool = False,
) -> dict[str, Any]:
    """Stop the running Odoo Docker environment.

    Args:
        remove_volumes: If true, also removes data volumes (DESTRUCTIVE — erases all data).
    """
    result = await docker.down(remove_volumes=remove_volumes)

    msg = "Odoo environment stopped."
    if remove_volumes:
        msg += " ⚠️ All data volumes were removed."

    return {
        "status": "stopped",
        "volumes_removed": remove_volumes,
        "message": msg,
    }


async def odoo_instance_restart(docker: OdooDocker) -> dict[str, Any]:
    """Restart the Odoo service (not PostgreSQL).

    Useful after configuration changes or to clear server state.
    """
    await docker.restart_service("web")
    await docker.wait_for_healthy(timeout=60)

    return {
        "status": "restarted",
        "message": "Odoo service restarted and healthy.",
    }


async def odoo_instance_status(docker: OdooDocker, rpc: OdooRPC) -> dict[str, Any]:
    """Returns health status of all containers.

    Shows container states, ports, and Odoo version.
    """
    try:
        status = await docker.status()
    except Exception as e:
        return {
            "running": False,
            "error": str(e),
            "message": "Docker containers are not running. Use odoo_instance_start to start them.",
        }

    # Try to get Odoo version
    version = "unknown"
    if status.get("running"):
        try:
            version = rpc.server_version()
        except Exception:
            pass

    return {
        "running": status.get("running", False),
        "odoo_version": version,
        "containers": status.get("containers", []),
        "url": "http://localhost:8069",
    }


async def odoo_instance_logs(
    docker: OdooDocker,
    lines: int = 100,
    level_filter: str | None = None,
    since: str | None = None,
    grep: str | None = None,
) -> dict[str, Any]:
    """Retrieve Odoo server logs.

    Args:
        lines: Number of recent log lines to fetch (default 100).
        level_filter: Filter by log level (e.g., "ERROR", "WARNING").
        since: Only show logs since this time (e.g., "5m", "1h", "2024-01-01").
        grep: Filter log lines by this regex pattern.
    """
    grep_pattern = grep
    if level_filter and not grep:
        grep_pattern = level_filter.upper()

    log_output = await docker.logs(
        service="web",
        lines=lines,
        since=since,
        grep=grep_pattern,
    )

    line_count = len(log_output.splitlines()) if log_output else 0

    # Truncate if very long
    if len(log_output) > 10000:
        log_output = log_output[-10000:]
        log_output = f"... (truncated, showing last 10000 chars)\n{log_output}"

    return {
        "lines_returned": line_count,
        "logs": log_output,
    }
