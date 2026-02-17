"""Integration setup workflow — configure external connections."""

from __future__ import annotations

from typing import Any

SUPPORTED_TYPES = {"email", "payment", "shipping"}


def setup_integration(
    integration_type: str,
    provider: str,
    db_name: str,
    settings: dict[str, Any],
    dry_run: bool = True,
) -> dict[str, Any]:
    """Generate a step-by-step plan for configuring an external integration.

    Supported integration types: email, payment, shipping.
    """
    if integration_type not in SUPPORTED_TYPES:
        return {
            "status": "error",
            "message": f"Unknown integration type '{integration_type}'",
            "supported_types": sorted(SUPPORTED_TYPES),
        }

    steps: list[dict[str, Any]] = []
    step_num = 1

    safe_name = f"{integration_type}_{provider}".lower().replace(" ", "_")

    # 1. Safety snapshot
    steps.append({
        "step": step_num,
        "tool": "odoo_snapshot_create",
        "params": {
            "db_name": db_name,
            "name": f"before_integration_{safe_name}",
            "description": f"Safety snapshot before {integration_type} integration ({provider})",
        },
        "description": "Create safety snapshot",
    })
    step_num += 1

    if integration_type == "email":
        steps.extend(_email_steps(db_name, provider, settings))
    elif integration_type == "payment":
        steps.extend(_payment_steps(db_name, provider, settings))
    elif integration_type == "shipping":
        steps.extend(_shipping_steps(db_name, provider, settings))

    # Re-number steps after extending
    for i, s in enumerate(steps):
        s["step"] = i + 1

    # Final health check
    steps.append({
        "step": len(steps) + 1,
        "tool": "odoo_diagnostics_health_check",
        "params": {"db_name": db_name},
        "description": "Run health check to verify integration",
    })

    return {
        "workflow": "setup_integration",
        "integration_type": integration_type,
        "provider": provider,
        "db_name": db_name,
        "steps": steps,
        "summary": {
            "total_steps": len(steps),
            "integration_type": integration_type,
            "provider": provider,
        },
        "dry_run": dry_run,
    }


def _email_steps(
    db_name: str, provider: str, settings: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate steps for email integration."""
    steps: list[dict[str, Any]] = []

    # Configure outgoing mail server
    steps.append({
        "step": 0,
        "tool": "odoo_email_configure_outgoing",
        "params": {
            "db_name": db_name,
            "smtp_host": settings.get("smtp_host", f"smtp.{provider}.com"),
            "smtp_port": settings.get("smtp_port", 587),
            "smtp_user": settings.get("smtp_user", ""),
            "smtp_pass": settings.get("smtp_pass", ""),
            "smtp_encryption": settings.get("smtp_encryption", "starttls"),
        },
        "description": f"Configure outgoing mail server ({provider})",
    })

    # Configure incoming mail server
    steps.append({
        "step": 0,
        "tool": "odoo_email_configure_incoming",
        "params": {
            "db_name": db_name,
            "server_type": settings.get("imap_type", "imap"),
            "host": settings.get("imap_host", f"imap.{provider}.com"),
            "port": settings.get("imap_port", 993),
            "user": settings.get("imap_user", settings.get("smtp_user", "")),
            "password": settings.get("imap_pass", settings.get("smtp_pass", "")),
            "ssl": settings.get("imap_ssl", True),
        },
        "description": f"Configure incoming mail server ({provider})",
    })

    # Test email
    steps.append({
        "step": 0,
        "tool": "odoo_email_test",
        "params": {"db_name": db_name},
        "description": "Test email configuration",
    })

    return steps


def _payment_steps(
    db_name: str, provider: str, settings: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate steps for payment provider integration."""
    steps: list[dict[str, Any]] = []

    # Map common providers to Odoo module names
    module_map: dict[str, str] = {
        "stripe": "payment_stripe",
        "paypal": "payment_paypal",
        "adyen": "payment_adyen",
        "authorize": "payment_authorize",
        "mollie": "payment_mollie",
    }
    module_name = module_map.get(provider.lower(), f"payment_{provider.lower()}")

    # Install payment module
    steps.append({
        "step": 0,
        "tool": "odoo_module_install",
        "params": {"db_name": db_name, "module_names": [module_name]},
        "description": f"Install payment module: {module_name}",
    })

    # Configure the payment provider
    steps.append({
        "step": 0,
        "tool": "odoo_record_create",
        "params": {
            "db_name": db_name,
            "model": "payment.provider",
            "values": {
                "name": provider.title(),
                "code": provider.lower(),
                "state": settings.get("state", "test"),
                **{k: v for k, v in settings.items() if k != "state"},
            },
        },
        "description": f"Configure {provider} payment provider",
    })

    return steps


def _shipping_steps(
    db_name: str, provider: str, settings: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate steps for shipping/delivery integration."""
    steps: list[dict[str, Any]] = []

    # Map common carriers to Odoo module names
    module_map: dict[str, str] = {
        "fedex": "delivery_fedex",
        "ups": "delivery_ups",
        "usps": "delivery_usps",
        "dhl": "delivery_dhl",
        "easypost": "delivery_easypost",
    }
    module_name = module_map.get(provider.lower(), f"delivery_{provider.lower()}")

    # Install delivery base + provider module
    steps.append({
        "step": 0,
        "tool": "odoo_module_install",
        "params": {"db_name": db_name, "module_names": ["delivery", module_name]},
        "description": f"Install delivery modules: delivery, {module_name}",
    })

    # Configure the carrier
    steps.append({
        "step": 0,
        "tool": "odoo_record_create",
        "params": {
            "db_name": db_name,
            "model": "delivery.carrier",
            "values": {
                "name": provider.title(),
                "delivery_type": provider.lower(),
                **settings,
            },
        },
        "description": f"Configure {provider} delivery carrier",
    })

    return steps
