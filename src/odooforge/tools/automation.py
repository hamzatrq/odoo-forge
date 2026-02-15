"""Automation tools — server actions, automated actions, email templates."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC
from odooforge.utils.validators import validate_model_name

logger = logging.getLogger(__name__)


async def odoo_automation_list(
    rpc: OdooRPC,
    db_name: str,
    model: str | None = None,
    trigger: str | None = None,
) -> dict[str, Any]:
    """List all automated actions (base.automation rules).

    Args:
        model: Filter by model.
        trigger: Filter by trigger (e.g., "on_create", "on_write", "on_time").
    """
    domain: list = []
    if model:
        validate_model_name(model)
        domain.append(("model_id.model", "=", model))
    if trigger:
        domain.append(("trigger", "=", trigger))

    rules = rpc.search_read(
        "base.automation",
        domain,
        fields=["name", "model_id", "trigger", "active", "action_server_ids",
                "trigger_field_ids", "filter_domain", "last_run"],
        limit=100,
        order="name asc",
        db=db_name,
    )

    return {
        "automations": [
            {
                "id": r["id"],
                "name": r.get("name", ""),
                "model": r["model_id"][1] if isinstance(r.get("model_id"), (list, tuple)) else "",
                "trigger": r.get("trigger", ""),
                "active": r.get("active", True),
                "action_count": len(r.get("action_server_ids", [])),
                "domain": r.get("filter_domain", ""),
            }
            for r in rules
        ],
        "count": len(rules),
    }


async def odoo_automation_create(
    rpc: OdooRPC,
    db_name: str,
    name: str,
    model: str,
    trigger: str,
    action_type: str = "code",
    code: str | None = None,
    filter_domain: str | None = None,
    trigger_fields: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new automated action (base.automation rule).

    Args:
        name: Human-readable name for the rule.
        model: Target model (e.g., "res.partner").
        trigger: When to fire: on_create, on_write, on_unlink, on_create_or_write, on_time.
        action_type: Type of action: code, object_write, followers, email, sms.
        code: Python code to execute (for action_type="code").
        filter_domain: Domain filter (only apply to matching records).
        trigger_fields: Field names that trigger the rule (for on_write).
    """
    validate_model_name(model)

    # Get model ID
    models = rpc.search_read(
        "ir.model",
        [["model", "=", model]],
        fields=["id"],
        limit=1,
        db=db_name,
    )
    if not models:
        return {"status": "error", "message": f"Model '{model}' not found."}

    model_id = models[0]["id"]

    # Create the server action first
    action_values: dict[str, Any] = {
        "name": f"{name} - Action",
        "model_id": model_id,
        "state": action_type,
        "type": "ir.actions.server",
    }
    if code and action_type == "code":
        action_values["code"] = code

    action_id = rpc.create("ir.actions.server", action_values, db=db_name)

    # Create the automation rule
    rule_values: dict[str, Any] = {
        "name": name,
        "model_id": model_id,
        "trigger": trigger,
        "action_server_ids": [(4, action_id)],
        "active": True,
    }

    if filter_domain:
        rule_values["filter_domain"] = filter_domain

    if trigger_fields and trigger in ("on_write", "on_create_or_write"):
        field_ids = rpc.search_read(
            "ir.model.fields",
            [["model", "=", model], ["name", "in", trigger_fields]],
            fields=["id"],
            db=db_name,
        )
        rule_values["trigger_field_ids"] = [(6, 0, [f["id"] for f in field_ids])]

    rule_id = rpc.create("base.automation", rule_values, db=db_name)

    return {
        "status": "created",
        "rule_id": rule_id,
        "action_id": action_id,
        "name": name,
        "model": model,
        "trigger": trigger,
        "action_type": action_type,
        "message": f"Automation rule '{name}' created (ID: {rule_id}).",
    }


async def odoo_automation_update(
    rpc: OdooRPC,
    db_name: str,
    rule_id: int,
    updates: dict,
) -> dict[str, Any]:
    """Update an existing automated action rule.

    Args:
        rule_id: ID of the automation rule.
        updates: Fields to update (e.g., {"active": false, "filter_domain": "..."}).
    """
    rules = rpc.read(
        "base.automation", [rule_id],
        fields=["name"],
        db=db_name,
    )
    if not rules:
        return {"status": "error", "message": f"Automation rule {rule_id} not found."}

    rpc.write("base.automation", [rule_id], updates, db=db_name)

    return {
        "status": "updated",
        "rule_id": rule_id,
        "name": rules[0]["name"],
        "updates": updates,
        "message": f"Automation rule '{rules[0]['name']}' updated.",
    }


async def odoo_automation_delete(
    rpc: OdooRPC,
    db_name: str,
    rule_id: int,
    confirm: bool = False,
) -> dict[str, Any]:
    """Delete an automated action rule.

    Args:
        rule_id: ID of the automation rule.
        confirm: Must be true to proceed.
    """
    if not confirm:
        return {"status": "cancelled", "message": "Set confirm=true to delete this automation."}

    rules = rpc.read("base.automation", [rule_id], fields=["name"], db=db_name)
    if not rules:
        return {"status": "error", "message": f"Automation rule {rule_id} not found."}

    rpc.unlink("base.automation", [rule_id], db=db_name)

    return {
        "status": "deleted",
        "rule_id": rule_id,
        "name": rules[0]["name"],
        "message": f"Automation rule '{rules[0]['name']}' deleted.",
    }


async def odoo_email_template_create(
    rpc: OdooRPC,
    db_name: str,
    name: str,
    model: str,
    subject: str,
    body_html: str,
    email_from: str | None = None,
    reply_to: str | None = None,
) -> dict[str, Any]:
    """Create an email template for use in automations or manual sends.

    Args:
        name: Template name.
        model: Target model (e.g., "res.partner").
        subject: Email subject (can use Jinja: {{ object.name }}).
        body_html: HTML body (can use Jinja: {{ object.email }}).
        email_from: Sender address.
        reply_to: Reply-to address.
    """
    validate_model_name(model)

    models = rpc.search_read(
        "ir.model",
        [["model", "=", model]],
        fields=["id"],
        limit=1,
        db=db_name,
    )
    if not models:
        return {"status": "error", "message": f"Model '{model}' not found."}

    values: dict[str, Any] = {
        "name": name,
        "model_id": models[0]["id"],
        "subject": subject,
        "body_html": body_html,
    }
    if email_from:
        values["email_from"] = email_from
    if reply_to:
        values["reply_to"] = reply_to

    template_id = rpc.create("mail.template", values, db=db_name)

    return {
        "status": "created",
        "template_id": template_id,
        "name": name,
        "model": model,
        "message": f"Email template '{name}' created (ID: {template_id}).",
    }
