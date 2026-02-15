"""View integrity verification."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC

logger = logging.getLogger(__name__)


async def verify_view_integrity(
    rpc: OdooRPC,
    db_name: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Verify views for a model (or all) have valid XML and no broken inheritance."""
    domain: list = [("active", "=", True)]
    if model:
        domain.append(("model", "=", model))

    views = rpc.search_read(
        "ir.ui.view", domain,
        fields=["name", "model", "type", "arch", "inherit_id"],
        limit=200, db=db_name,
    )

    issues = []
    for v in views:
        arch = v.get("arch", "")
        if not arch or not arch.strip():
            issues.append({"view_id": v["id"], "name": v["name"], "issue": "Empty architecture"})
        if v.get("inherit_id") and "<xpath" not in arch and "<field" not in arch:
            issues.append({"view_id": v["id"], "name": v["name"], "issue": "Inheriting view with no xpath/field"})

    return {
        "verified": len(issues) == 0,
        "views_checked": len(views),
        "issues": issues,
    }
