"""Snapshot tools — create, list, restore, delete."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.docker_client import OdooDocker
from odooforge.connections.xmlrpc_client import OdooRPC
from odooforge.utils.validators import validate_db_name
from odooforge.verification.state_cache import LiveStateCache

logger = logging.getLogger(__name__)


async def odoo_snapshot_create(
    docker: OdooDocker,
    db_name: str,
    name: str,
    description: str = "",
) -> dict[str, Any]:
    """Create a named snapshot (backup) of a database.

    Snapshots can be restored later to roll back changes.
    Use before risky operations like module installs or view modifications.

    Args:
        db_name: Database to snapshot.
        name: Unique name for this snapshot (e.g., "before_sale_install").
        description: Optional description of what this snapshot captures.
    """
    validate_db_name(db_name)

    if not name:
        return {"status": "error", "message": "Snapshot name is required."}

    # Check if name already exists
    existing = await docker.list_snapshots()
    if any(s["name"] == name for s in existing):
        return {
            "status": "error",
            "message": f"Snapshot '{name}' already exists. Use a different name or delete it first.",
        }

    manifest = await docker.create_snapshot(db_name, name, description)

    size_mb = round(manifest.get("size_bytes", 0) / 1024 / 1024, 2)

    return {
        "status": "created",
        "snapshot": name,
        "database": db_name,
        "size_mb": size_mb,
        "created_at": manifest.get("created_at"),
        "message": f"Snapshot '{name}' created ({size_mb} MB). Use odoo_snapshot_restore to roll back.",
    }


async def odoo_snapshot_list(
    docker: OdooDocker,
    db_name: str | None = None,
) -> dict[str, Any]:
    """List all available snapshots, optionally filtered by database.

    Args:
        db_name: If provided, only show snapshots for this database.
    """
    snapshots = await docker.list_snapshots(db=db_name)

    items = []
    for s in snapshots:
        items.append({
            "name": s.get("name"),
            "database": s.get("database"),
            "created_at": s.get("created_at"),
            "size_mb": round(s.get("size_bytes", 0) / 1024 / 1024, 2),
            "description": s.get("description", ""),
        })

    return {
        "snapshots": items,
        "count": len(items),
    }


async def odoo_snapshot_restore(
    docker: OdooDocker,
    rpc: OdooRPC,
    cache: LiveStateCache,
    db_name: str,
    snapshot_name: str,
) -> dict[str, Any]:
    """Restore a database from a previously created snapshot.

    ⚠️ This replaces the current database contents entirely.
    The Odoo service will be restarted after restoration.

    Args:
        db_name: Target database to restore into.
        snapshot_name: Name of the snapshot to restore.
    """
    validate_db_name(db_name)

    await docker.restore_snapshot(db_name, snapshot_name)

    # Re-authenticate and refresh cache
    try:
        rpc.authenticate(db_name)
        cache.refresh_all()
    except Exception as e:
        logger.warning("Post-restore auth failed (may need manual reconnect): %s", e)

    return {
        "status": "restored",
        "database": db_name,
        "from_snapshot": snapshot_name,
        "message": (
            f"Database '{db_name}' restored from snapshot '{snapshot_name}'. "
            "Odoo has been restarted. All authenticated sessions are refreshed."
        ),
    }


async def odoo_snapshot_delete(
    docker: OdooDocker,
    name: str,
) -> dict[str, Any]:
    """Delete a snapshot from disk.

    Args:
        name: Name of the snapshot to delete.
    """
    result = await docker.delete_snapshot(name)

    freed_mb = round(result.get("freed_bytes", 0) / 1024 / 1024, 2)

    return {
        "status": "deleted",
        "snapshot": name,
        "freed_mb": freed_mb,
        "message": f"Snapshot '{name}' deleted ({freed_mb} MB freed).",
    }
