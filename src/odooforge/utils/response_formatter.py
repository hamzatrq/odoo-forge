"""Response formatting utilities for consistent, rich MCP tool responses."""

from __future__ import annotations

from typing import Any


def success(message: str, **extra: Any) -> dict[str, Any]:
    """Create a standardized success response."""
    return {"status": "ok", "message": message, **extra}


def error(
    message: str,
    suggestion: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Create a standardized error response with optional suggestion."""
    result: dict[str, Any] = {"status": "error", "message": message}
    if suggestion:
        result["suggestion"] = suggestion
    result.update(extra)
    return result


def paginated(
    items: list[dict],
    total: int,
    offset: int = 0,
    limit: int = 100,
    item_key: str = "items",
) -> dict[str, Any]:
    """Create a paginated response."""
    has_more = offset + limit < total,
    return {
        item_key: items,
        "count": len(items),
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
    }


def confirm_required(
    action: str,
    target: str,
    details: dict | None = None,
) -> dict[str, Any]:
    """Response indicating confirmation is required for a destructive action."""
    return {
        "status": "confirmation_required",
        "action": action,
        "target": target,
        "message": f"Set confirm=True to {action} '{target}'.",
        **({"details": details} if details else {}),
    }


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs:.0f}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"
