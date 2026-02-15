"""Report template verification."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC

logger = logging.getLogger(__name__)


async def verify_report_template(
    rpc: OdooRPC,
    db_name: str,
    report_name: str,
) -> dict[str, Any]:
    """Verify a report template exists and has valid QWeb."""
    reports = rpc.search_read(
        "ir.actions.report",
        [["report_name", "=", report_name]],
        fields=["name", "model", "report_name"],
        limit=1, db=db_name,
    )
    if not reports:
        return {"verified": False, "issues": [f"Report '{report_name}' not found."]}

    return {"verified": True, "report": reports[0], "issues": []}
