"""Automation rule verification."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC

logger = logging.getLogger(__name__)


async def verify_automation_rule(
    rpc: OdooRPC,
    db_name: str,
    rule_id: int,
) -> dict[str, Any]:
    """Verify an automation rule is correctly configured and active."""
    rules = rpc.read(
        "base.automation", [rule_id],
        fields=["name", "active", "trigger", "model_id", "action_server_ids"],
        db=db_name,
    )
    if not rules:
        return {"verified": False, "issues": [f"Rule {rule_id} not found."]}

    rule = rules[0]
    issues = []
    if not rule.get("active"):
        issues.append("Rule is inactive.")
    if not rule.get("action_server_ids"):
        issues.append("No server actions linked — rule will do nothing.")

    return {
        "verified": len(issues) == 0,
        "rule": {"id": rule_id, "name": rule["name"], "trigger": rule["trigger"]},
        "issues": issues,
    }
