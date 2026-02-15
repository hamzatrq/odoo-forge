"""Direct PostgreSQL access for diagnostics and fast queries."""

from __future__ import annotations

import logging
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class PGError(Exception):
    """Raised when a PostgreSQL operation fails."""


class OdooPG:
    """Direct PostgreSQL access for diagnostics and operations.

    Used for fast read-only queries that bypass Odoo's ORM,
    and for database-level diagnostics (sizes, integrity checks).
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        user: str = "odoo",
        password: str = "odoo",
        database: str = "postgres",
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self, database: str | None = None) -> asyncpg.Pool:
        """Get or create connection pool."""
        db = database or self.database
        # If database changed or pool doesn't exist, create new pool
        if self._pool is None or db != self.database:
            if self._pool is not None:
                await self._pool.close()
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=db,
                min_size=1,
                max_size=5,
            )
            self.database = db
        return self._pool

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    # ── Query methods ───────────────────────────────────────────────

    async def query(
        self, sql: str, params: list | None = None, database: str | None = None
    ) -> list[dict]:
        """Execute a SELECT query, return rows as dicts."""
        pool = await self._get_pool(database)
        try:
            async with pool.acquire() as conn:
                if params:
                    rows = await conn.fetch(sql, *params)
                else:
                    rows = await conn.fetch(sql)
                return [dict(row) for row in rows]
        except asyncpg.PostgresError as e:
            raise PGError(f"Query failed: {e}") from e

    async def execute(
        self, sql: str, params: list | None = None, database: str | None = None
    ) -> str:
        """Execute an INSERT/UPDATE/DELETE, return status string."""
        pool = await self._get_pool(database)
        try:
            async with pool.acquire() as conn:
                if params:
                    return await conn.execute(sql, *params)
                return await conn.execute(sql)
        except asyncpg.PostgresError as e:
            raise PGError(f"Execute failed: {e}") from e

    # ── Odoo-specific convenience queries ──────────────────────────

    async def get_installed_modules(self, database: str | None = None) -> list[dict]:
        """Fast module status query (bypasses Odoo ORM)."""
        return await self.query(
            "SELECT name, state, latest_version "
            "FROM ir_module_module "
            "WHERE state = 'installed' "
            "ORDER BY name",
            database=database,
        )

    async def get_db_size(self, database: str | None = None) -> str:
        """Database size in human-readable format."""
        db = database or self.database
        rows = await self.query(
            "SELECT pg_size_pretty(pg_database_size($1)) AS size",
            [db],
            database="postgres",
        )
        return rows[0]["size"] if rows else "unknown"

    async def get_table_sizes(
        self, limit: int = 20, database: str | None = None
    ) -> list[dict]:
        """Largest tables for diagnostics."""
        return await self.query(
            "SELECT relname AS table_name, "
            "pg_size_pretty(pg_total_relation_size(C.oid)) AS total_size, "
            "pg_total_relation_size(C.oid) AS size_bytes "
            "FROM pg_class C "
            "LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace) "
            "WHERE nspname = 'public' AND C.relkind = 'r' "
            "ORDER BY pg_total_relation_size(C.oid) DESC "
            "LIMIT $1",
            [limit],
            database=database,
        )

    async def check_view_integrity(self, database: str | None = None) -> list[dict]:
        """Find views with potential issues (orphaned inherit_id, etc.)."""
        return await self.query(
            "SELECT v.id, v.name, v.model, v.type, v.inherit_id, "
            "  CASE WHEN v.inherit_id IS NOT NULL AND p.id IS NULL "
            "    THEN 'orphaned_inherit' "
            "    ELSE 'ok' "
            "  END AS status "
            "FROM ir_ui_view v "
            "LEFT JOIN ir_ui_view p ON v.inherit_id = p.id "
            "WHERE v.inherit_id IS NOT NULL AND p.id IS NULL "
            "ORDER BY v.model, v.name",
            database=database,
        )

    async def list_databases(self) -> list[str]:
        """List all non-template databases."""
        rows = await self.query(
            "SELECT datname FROM pg_database "
            "WHERE datistemplate = false AND datname != 'postgres' "
            "ORDER BY datname",
            database="postgres",
        )
        return [row["datname"] for row in rows]
