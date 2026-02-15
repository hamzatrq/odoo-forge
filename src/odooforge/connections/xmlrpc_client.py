"""XML-RPC client wrapper for Odoo with session caching and retry logic."""

from __future__ import annotations

import logging
import time
import xmlrpc.client
from typing import Any

logger = logging.getLogger(__name__)


class OdooRPCError(Exception):
    """Raised when an Odoo XML-RPC call fails."""

    def __init__(self, message: str, fault_code: str | None = None):
        self.fault_code = fault_code
        super().__init__(message)


class OdooRPC:
    """Thread-safe XML-RPC wrapper for Odoo with session caching.

    All high-level Odoo data operations go through this client.
    """

    def __init__(self, url: str, db: str = "", username: str = "admin", password: str = "admin"):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self.uid: int | None = None
        self._common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", allow_none=True
        )
        self._object = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", allow_none=True
        )

    # ── Authentication ──────────────────────────────────────────────

    def authenticate(self, db: str | None = None) -> int:
        """Authenticate and cache uid. Raises OdooRPCError on failure."""
        target_db = db or self.db
        if not target_db:
            raise OdooRPCError("No database specified for authentication")

        try:
            uid = self._common.authenticate(target_db, self.username, self.password, {})
        except xmlrpc.client.Fault as e:
            raise OdooRPCError(f"Authentication fault: {e.faultString}", e.faultCode) from e
        except Exception as e:
            raise OdooRPCError(f"Cannot connect to Odoo at {self.url}: {e}") from e

        if not uid:
            raise OdooRPCError(
                f"Authentication failed for user '{self.username}' on database '{target_db}'. "
                "Check credentials."
            )

        self.uid = uid
        if db:
            self.db = target_db
        return uid

    def _ensure_auth(self, db: str | None = None) -> tuple[str, int]:
        """Ensure we're authenticated, re-auth if db changed."""
        target_db = db or self.db
        if not target_db:
            raise OdooRPCError("No database specified")

        if self.uid is None or target_db != self.db:
            self.authenticate(target_db)

        return target_db, self.uid  # type: ignore[return-value]

    # ── Core execute ────────────────────────────────────────────────

    def execute(
        self,
        model: str,
        method: str,
        *args: Any,
        db: str | None = None,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> Any:
        """Generic execute_kw wrapper with retry logic."""
        target_db, uid = self._ensure_auth(db)

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                return self._object.execute_kw(
                    target_db, uid, self.password, model, method,
                    list(args) if args else [],
                    kwargs if kwargs else {},
                )
            except xmlrpc.client.Fault as e:
                raise OdooRPCError(
                    f"Odoo error on {model}.{method}: {e.faultString}",
                    e.faultCode,
                ) from e
            except (ConnectionError, OSError, xmlrpc.client.ProtocolError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        "Connection error on %s.%s (attempt %d/%d), retrying in %ds: %s",
                        model, method, attempt + 1, max_retries, wait, e,
                    )
                    time.sleep(wait)
                    # Re-authenticate in case Odoo restarted
                    self.uid = None
                    self._ensure_auth(target_db)

        raise OdooRPCError(f"Failed after {max_retries} attempts: {last_error}") from last_error

    # ── Convenience methods ─────────────────────────────────────────

    def search_read(
        self,
        model: str,
        domain: list,
        fields: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
        order: str | None = None,
        db: str | None = None,
    ) -> list[dict]:
        """Search + read in one call."""
        kwargs: dict[str, Any] = {"limit": limit, "offset": offset}
        if fields:
            kwargs["fields"] = fields
        if order:
            kwargs["order"] = order

        return self.execute(model, "search_read", domain, db=db, **kwargs)

    def search_count(self, model: str, domain: list, db: str | None = None) -> int:
        """Count records matching domain."""
        return self.execute(model, "search_count", domain, db=db)

    def create(self, model: str, values: dict | list[dict], db: str | None = None) -> int | list[int]:
        """Create record(s)."""
        if isinstance(values, list):
            return self.execute(model, "create", values, db=db)
        return self.execute(model, "create", [values], db=db)

    def read(
        self,
        model: str,
        ids: list[int],
        fields: list[str] | None = None,
        db: str | None = None,
    ) -> list[dict]:
        """Read specific records by ID."""
        kwargs: dict[str, Any] = {}
        if fields:
            kwargs["fields"] = fields
        return self.execute(model, "read", ids, db=db, **kwargs)

    def write(self, model: str, ids: list[int], values: dict, db: str | None = None) -> bool:
        """Update record(s)."""
        return self.execute(model, "write", ids, values, db=db)

    def unlink(self, model: str, ids: list[int], db: str | None = None) -> bool:
        """Delete record(s)."""
        return self.execute(model, "unlink", ids, db=db)

    def fields_get(
        self,
        model: str,
        attributes: list[str] | None = None,
        db: str | None = None,
    ) -> dict:
        """Introspect model fields — the core truth source."""
        kwargs: dict[str, Any] = {}
        if attributes:
            kwargs["attributes"] = attributes
        return self.execute(model, "fields_get", db=db, **kwargs)

    def load(
        self,
        model: str,
        fields: list[str],
        data: list[list],
        db: str | None = None,
    ) -> dict:
        """Bulk import using Odoo's native load() method.

        Returns: {"ids": [...], "messages": [...]}
        """
        return self.execute(model, "load", fields, data, db=db)

    def execute_method(
        self,
        model: str,
        method: str,
        args: list | None = None,
        kwargs: dict | None = None,
        db: str | None = None,
    ) -> Any:
        """Call any model method (generic escape hatch)."""
        target_db, uid = self._ensure_auth(db)
        call_args = args or []
        call_kwargs = kwargs or {}

        return self._object.execute_kw(
            target_db, uid, self.password, model, method,
            call_args, call_kwargs,
        )

    # ── View-specific helpers ───────────────────────────────────────

    def get_view(
        self,
        model: str,
        view_type: str = "form",
        view_id: int | None = None,
        db: str | None = None,
    ) -> dict:
        """Get compiled view arch via get_view()."""
        kwargs: dict[str, Any] = {"view_type": view_type}
        if view_id:
            kwargs["view_id"] = view_id
        return self.execute(model, "get_view", db=db, **kwargs)

    def create_inheriting_view(
        self,
        model: str,
        parent_view_id: int,
        name: str,
        arch: str,
        priority: int = 99,
        db: str | None = None,
    ) -> int:
        """Create a new ir.ui.view record that inherits from parent."""
        return self.create(
            "ir.ui.view",
            {
                "name": name,
                "model": model,
                "inherit_id": parent_view_id,
                "arch": arch,
                "priority": priority,
            },
            db=db,
        )

    # ── Server info ─────────────────────────────────────────────────

    def server_version(self) -> str:
        """Get Odoo server version."""
        try:
            return str(self._common.version()["server_version"])
        except Exception as e:
            raise OdooRPCError(f"Cannot get server version: {e}") from e

    # ── Database management (via /xmlrpc/2/db) ──────────────────────

    def _db_proxy(self) -> xmlrpc.client.ServerProxy:
        """Get the database management proxy."""
        return xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/db", allow_none=True)

    def db_list(self) -> list[str]:
        """List all databases."""
        try:
            return self._db_proxy().list()
        except Exception as e:
            raise OdooRPCError(f"Cannot list databases: {e}") from e

    def db_create(
        self,
        master_password: str,
        db_name: str,
        demo: bool = False,
        lang: str = "en_US",
        user_password: str = "admin",
        login: str = "admin",
        country_code: str | None = None,
    ) -> bool:
        """Create a new database."""
        try:
            return self._db_proxy().create_database(
                master_password, db_name, demo, lang, user_password, login,
                country_code or False,
            )
        except xmlrpc.client.Fault as e:
            raise OdooRPCError(f"Database creation failed: {e.faultString}") from e

    def db_drop(self, master_password: str, db_name: str) -> bool:
        """Drop a database."""
        try:
            return self._db_proxy().drop(master_password, db_name)
        except xmlrpc.client.Fault as e:
            raise OdooRPCError(f"Database drop failed: {e.faultString}") from e

    def db_exists(self, db_name: str) -> bool:
        """Check if a database exists."""
        return db_name in self.db_list()
