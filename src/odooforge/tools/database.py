"""Database management tools — create, list, backup, restore, drop, run_sql."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.docker_client import OdooDocker
from odooforge.connections.pg_client import OdooPG
from odooforge.connections.xmlrpc_client import OdooRPC
from odooforge.utils.validators import validate_db_name
from odooforge.verification.state_cache import LiveStateCache

logger = logging.getLogger(__name__)


async def odoo_db_create(
    rpc: OdooRPC,
    cache: LiveStateCache,
    master_password: str,
    db_name: str,
    language: str = "en_US",
    country: str | None = None,
    demo_data: bool = False,
    admin_password: str = "admin",
) -> dict[str, Any]:
    """Create a new Odoo database and initialize the base module.

    Args:
        db_name: Name for the new database.
        language: Language code (default "en_US").
        country: Country code (e.g., "PK" for Pakistan).
        demo_data: If true, load demo/sample data.
        admin_password: Password for the admin user.
    """
    validate_db_name(db_name)

    # Check if DB already exists
    if rpc.db_exists(db_name):
        return {
            "status": "already_exists",
            "db_name": db_name,
            "message": f"Database '{db_name}' already exists. Use a different name or drop it first.",
        }

    rpc.db_create(
        master_password=master_password,
        db_name=db_name,
        demo=demo_data,
        lang=language,
        user_password=admin_password,
        country_code=country,
    )

    # Authenticate against the new db
    rpc.authenticate(db_name)

    # Initialize cache
    cache.refresh_modules()

    return {
        "status": "created",
        "db_name": db_name,
        "language": language,
        "country": country or "not set",
        "demo_data": demo_data,
        "admin_user": "admin",
        "message": f"Database '{db_name}' created successfully. Authenticated as admin.",
    }


async def odoo_db_list(rpc: OdooRPC) -> dict[str, Any]:
    """List all databases on the Odoo instance."""
    databases = rpc.db_list()
    return {
        "databases": databases,
        "count": len(databases),
    }


async def odoo_db_backup(
    docker: OdooDocker,
    db_name: str,
) -> dict[str, Any]:
    """Create a backup of a database.

    Uses pg_dump via Docker for reliable, fast backups.
    """
    validate_db_name(db_name)

    snapshot = await docker.create_snapshot(
        db=db_name,
        name=f"backup_{db_name}",
        description=f"Manual backup of {db_name}",
    )

    return {
        "status": "backed_up",
        "db_name": db_name,
        "snapshot_name": snapshot["name"],
        "size_bytes": snapshot.get("size_bytes", 0),
        "created_at": snapshot.get("created_at"),
        "message": f"Backup created as snapshot '{snapshot['name']}'.",
    }


async def odoo_db_restore(
    docker: OdooDocker,
    rpc: OdooRPC,
    cache: LiveStateCache,
    db_name: str,
    backup_name: str,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Restore a database from a backup.

    Args:
        db_name: Target database name.
        backup_name: Name of the snapshot to restore from.
        overwrite: Must be true to overwrite an existing database.
    """
    validate_db_name(db_name)

    if rpc.db_exists(db_name) and not overwrite:
        return {
            "status": "error",
            "message": f"Database '{db_name}' already exists. Set overwrite=true to replace it.",
        }

    result = await docker.restore_snapshot(db=db_name, name=backup_name)

    # Re-authenticate and refresh cache
    rpc.authenticate(db_name)
    cache.refresh_all()

    return {
        "status": "restored",
        "db_name": db_name,
        "from_snapshot": backup_name,
        "message": f"Database '{db_name}' restored from snapshot '{backup_name}'.",
    }


async def odoo_db_drop(
    rpc: OdooRPC,
    master_password: str,
    db_name: str,
    confirm: bool = False,
) -> dict[str, Any]:
    """Drop a database permanently.

    Args:
        db_name: Database to drop.
        confirm: Must be true to confirm deletion.
    """
    if not confirm:
        return {
            "status": "cancelled",
            "message": "Set confirm=true to permanently drop this database. This cannot be undone.",
        }

    validate_db_name(db_name)

    if not rpc.db_exists(db_name):
        return {
            "status": "not_found",
            "message": f"Database '{db_name}' does not exist.",
        }

    rpc.db_drop(master_password, db_name)

    return {
        "status": "dropped",
        "db_name": db_name,
        "message": f"Database '{db_name}' has been permanently deleted.",
    }


async def odoo_db_run_sql(
    pg: OdooPG,
    db_name: str,
    query: str,
    params: list | None = None,
) -> dict[str, Any]:
    """Execute a raw SQL query against a database.

    Args:
        db_name: Target database.
        query: SQL query to execute.
        params: Optional query parameters (positional, $1 $2 style).

    ⚠️ Use with caution — this bypasses Odoo's ORM.
    """
    validate_db_name(db_name)

    is_read = query.strip().upper().startswith(("SELECT", "WITH", "EXPLAIN", "SHOW"))

    if is_read:
        rows = await pg.query(query, params, database=db_name)
        return {
            "status": "ok",
            "row_count": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
            "rows": rows[:100],  # Cap at 100 rows
            "truncated": len(rows) > 100,
        }
    else:
        result = await pg.execute(query, params, database=db_name)
        return {
            "status": "ok",
            "result": result,
            "message": "Query executed successfully.",
        }
