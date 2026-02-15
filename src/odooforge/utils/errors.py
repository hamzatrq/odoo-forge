"""Custom error classes with actionable messages and fault enrichment."""

from __future__ import annotations

from typing import Any


class OdooForgeError(Exception):
    """Base exception for all OdooForge errors."""

    def __init__(self, message: str, suggestion: str = "", code: str = "UNKNOWN"):
        self.suggestion = suggestion
        self.code = code
        full = message
        if suggestion:
            full = f"{message}\n💡 Suggestion: {suggestion}"
        super().__init__(full)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"status": "error", "code": self.code, "message": str(self)}
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


class ConnectionError(OdooForgeError):
    """Cannot connect to Odoo or PostgreSQL."""


class AuthenticationError(OdooForgeError):
    """Authentication failed."""


class DatabaseError(OdooForgeError):
    """Database operation failed."""


class ModuleError(OdooForgeError):
    """Module install/upgrade/uninstall failed."""


class ValidationError(OdooForgeError):
    """Input validation failed (bad field names, invalid domain, etc.)."""


class ViewError(OdooForgeError):
    """View modification or verification failed."""


class SnapshotError(OdooForgeError):
    """Snapshot create/restore failed."""


class DockerNotRunningError(OdooForgeError):
    """Docker containers are not running."""

    def __init__(self):
        super().__init__(
            "Odoo Docker containers are not running.",
            "Run odoo_instance_start to start the environment, "
            "or check that Docker Desktop is running.",
            code="DOCKER_NOT_RUNNING",
        )


# ── XML-RPC fault enrichment ─────────────────────────────────────

FAULT_SUGGESTIONS: dict[str, str] = {
    "AccessDenied": "Check credentials or user permissions.",
    "AccessError": "Current user lacks permission. Try admin or check access rights.",
    "MissingError": "The record may have been deleted. Refresh your data.",
    "ValidationError": "A required field is missing or invalid. Check constraints.",
    "UserError": "Operation not allowed in current state. Check workflow.",
    "UniqueViolation": "A record with this value already exists.",
    "ForeignKeyViolation": "Record is referenced by others. Remove dependents first.",
}


def enrich_rpc_error(fault_string: str) -> dict[str, Any]:
    """Enrich an XML-RPC fault with actionable suggestions."""
    for key, suggestion in FAULT_SUGGESTIONS.items():
        if key in fault_string:
            return {"status": "error", "code": key,
                    "message": fault_string[:500], "suggestion": suggestion}
    return {"status": "error", "code": "RPC_ERROR",
            "message": fault_string[:500],
            "suggestion": "Check logs with odoo_instance_logs for details."}
