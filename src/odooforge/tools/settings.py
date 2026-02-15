"""Settings and company tools — get/set config, company setup, user management."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC

logger = logging.getLogger(__name__)


async def odoo_settings_get(
    rpc: OdooRPC,
    db_name: str,
    keys: list[str] | None = None,
) -> dict[str, Any]:
    """Get current system settings (res.config.settings).

    Args:
        keys: Specific setting keys to retrieve. If None, returns all.
    """
    try:
        # Create a temp config wizard to read settings
        config_id = rpc.create("res.config.settings", {}, db=db_name)
        settings = rpc.read(
            "res.config.settings", [config_id],
            fields=keys or [],
            db=db_name,
        )

        if not settings:
            return {"status": "error", "message": "Could not read settings."}

        result = settings[0]
        # Clean out internal fields
        for k in ("id", "__last_update", "create_uid", "create_date", "write_uid", "write_date"):
            result.pop(k, None)

        if keys:
            result = {k: v for k, v in result.items() if k in keys}

        return {
            "status": "ok",
            "settings": result,
            "count": len(result),
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to read settings: {e}"}


async def odoo_settings_set(
    rpc: OdooRPC,
    db_name: str,
    values: dict,
) -> dict[str, Any]:
    """Update system settings.

    Args:
        values: Dictionary of setting key-value pairs to set.
    """
    if not values:
        return {"status": "error", "message": "No values provided."}

    try:
        config_id = rpc.create("res.config.settings", values, db=db_name)
        rpc.execute_method("res.config.settings", "execute", [[config_id]], db=db_name)

        return {
            "status": "updated",
            "settings": {k: "***" if "password" in k.lower() else v for k, v in values.items()},
            "message": f"Updated {len(values)} setting(s). Settings applied.",
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to update settings: {e}"}


async def odoo_company_configure(
    rpc: OdooRPC,
    db_name: str,
    updates: dict,
) -> dict[str, Any]:
    """Configure the main company details.

    Args:
        updates: Company fields to update. Common fields:
            name, street, city, zip, country_id, phone, email,
            website, vat, currency_id, logo (base64).
    """
    if not updates:
        return {"status": "error", "message": "No updates provided."}

    companies = rpc.search_read(
        "res.company",
        [],
        fields=["id", "name"],
        limit=1,
        db=db_name,
    )
    if not companies:
        return {"status": "error", "message": "No company found."}

    company = companies[0]
    rpc.write("res.company", [company["id"]], updates, db=db_name)

    return {
        "status": "configured",
        "company_id": company["id"],
        "company_name": company["name"],
        "updates": {k: "..." if k == "logo" else v for k, v in updates.items()},
        "message": f"Company '{company['name']}' configured with {len(updates)} update(s).",
    }


async def odoo_users_manage(
    rpc: OdooRPC,
    db_name: str,
    action: str = "list",
    user_id: int | None = None,
    values: dict | None = None,
) -> dict[str, Any]:
    """Manage Odoo users — list, create, update, activate/deactivate.

    Args:
        action: "list", "create", "update", "activate", "deactivate".
        user_id: User ID (for update/activate/deactivate).
        values: User data (for create/update). Fields: name, login, email, groups_id.
    """
    if action == "list":
        users = rpc.search_read(
            "res.users",
            [["share", "=", False]],
            fields=["name", "login", "email", "active", "groups_id"],
            limit=100,
            db=db_name,
        )
        return {
            "users": [
                {
                    "id": u["id"],
                    "name": u.get("name", ""),
                    "login": u.get("login", ""),
                    "email": u.get("email", ""),
                    "active": u.get("active", True),
                }
                for u in users
            ],
            "count": len(users),
        }

    elif action == "create":
        if not values or "name" not in values or "login" not in values:
            return {"status": "error", "message": "name and login are required for creating a user."}

        user_id = rpc.create("res.users", values, db=db_name)
        return {
            "status": "created",
            "user_id": user_id,
            "name": values["name"],
            "login": values["login"],
            "message": f"User '{values['name']}' created (ID: {user_id}).",
        }

    elif action == "update":
        if not user_id or not values:
            return {"status": "error", "message": "user_id and values required for update."}

        rpc.write("res.users", [user_id], values, db=db_name)
        return {"status": "updated", "user_id": user_id, "message": f"User {user_id} updated."}

    elif action in ("activate", "deactivate"):
        if not user_id:
            return {"status": "error", "message": "user_id required."}

        active = action == "activate"
        rpc.write("res.users", [user_id], {"active": active}, db=db_name)
        return {
            "status": action + "d",
            "user_id": user_id,
            "message": f"User {user_id} {'activated' if active else 'deactivated'}.",
        }

    else:
        return {"status": "error", "message": f"Unknown action: {action}. Use list/create/update/activate/deactivate."}
