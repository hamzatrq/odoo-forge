"""Email configuration tools — SMTP outgoing, incoming, test, DNS guide."""

from __future__ import annotations

import logging
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC

logger = logging.getLogger(__name__)


async def odoo_email_configure_outgoing(
    rpc: OdooRPC,
    db_name: str,
    name: str,
    smtp_host: str,
    smtp_port: int = 587,
    smtp_user: str | None = None,
    smtp_pass: str | None = None,
    smtp_encryption: str = "starttls",
    email_from: str | None = None,
) -> dict[str, Any]:
    """Configure an outgoing SMTP mail server.

    Args:
        name: Server name (e.g., "Company Gmail").
        smtp_host: SMTP hostname (e.g., "smtp.gmail.com").
        smtp_port: SMTP port (default: 587 for STARTTLS).
        smtp_user: SMTP username/email.
        smtp_pass: SMTP password or app password.
        smtp_encryption: "starttls", "ssl", or "none".
        email_from: Default sender address.
    """
    values: dict[str, Any] = {
        "name": name,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_encryption": smtp_encryption,
        "active": True,
    }
    if smtp_user:
        values["smtp_user"] = smtp_user
    if smtp_pass:
        values["smtp_pass"] = smtp_pass
    if email_from:
        values["email_from"] = email_from

    # Check if server already exists
    existing = rpc.search_read(
        "ir.mail_server",
        [["name", "=", name]],
        fields=["id"],
        limit=1,
        db=db_name,
    )

    if existing:
        rpc.write("ir.mail_server", [existing[0]["id"]], values, db=db_name)
        return {
            "status": "updated",
            "server_id": existing[0]["id"],
            "name": name,
            "message": f"Outgoing mail server '{name}' updated.",
        }

    server_id = rpc.create("ir.mail_server", values, db=db_name)
    return {
        "status": "created",
        "server_id": server_id,
        "name": name,
        "host": smtp_host,
        "port": smtp_port,
        "encryption": smtp_encryption,
        "message": f"Outgoing mail server '{name}' created. Test with odoo_email_test.",
    }


async def odoo_email_configure_incoming(
    rpc: OdooRPC,
    db_name: str,
    name: str,
    server_type: str = "imap",
    host: str = "",
    port: int = 993,
    user: str = "",
    password: str = "",
    ssl: bool = True,
) -> dict[str, Any]:
    """Configure an incoming mail server (IMAP/POP3) for fetching emails.

    Args:
        name: Server name.
        server_type: "imap" or "pop".
        host: Mail server hostname.
        port: Server port (default: 993 for IMAPS).
        user: Login username.
        password: Login password.
        ssl: Use SSL/TLS.
    """
    values: dict[str, Any] = {
        "name": name,
        "server_type": server_type,
        "server": host,
        "port": port,
        "user": user,
        "password": password,
        "is_ssl": ssl,
        "active": True,
        "state": "draft",
    }

    existing = rpc.search_read(
        "fetchmail.server",
        [["name", "=", name]],
        fields=["id"],
        limit=1,
        db=db_name,
    )

    if existing:
        rpc.write("fetchmail.server", [existing[0]["id"]], values, db=db_name)
        return {
            "status": "updated",
            "server_id": existing[0]["id"],
            "message": f"Incoming mail server '{name}' updated.",
        }

    server_id = rpc.create("fetchmail.server", values, db=db_name)
    return {
        "status": "created",
        "server_id": server_id,
        "name": name,
        "type": server_type,
        "host": host,
        "message": f"Incoming mail server '{name}' created.",
    }


async def odoo_email_test(
    rpc: OdooRPC,
    db_name: str,
    to_address: str,
    subject: str = "OdooForge Test Email",
    body: str = "This is a test email from OdooForge.",
) -> dict[str, Any]:
    """Send a test email to verify outgoing mail configuration.

    Args:
        to_address: Recipient email address.
        subject: Email subject.
        body: Email body text.
    """
    try:
        mail_id = rpc.create("mail.mail", {
            "subject": subject,
            "body_html": f"<p>{body}</p>",
            "email_to": to_address,
            "auto_delete": True,
        }, db=db_name)

        rpc.execute_method("mail.mail", "send", [[mail_id]], db=db_name)

        return {
            "status": "sent",
            "mail_id": mail_id,
            "to": to_address,
            "message": f"Test email sent to {to_address}. Check inbox and spam folder.",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send test email: {e}",
            "suggestion": "Check SMTP configuration. Common issues: wrong credentials, "
                          "require app-specific password, or firewall blocking port.",
        }


async def odoo_email_dns_guide(
    domain: str,
) -> dict[str, Any]:
    """Generate DNS records guide for email deliverability (SPF, DKIM, DMARC).

    Args:
        domain: Your email domain (e.g., "example.com").
    """
    return {
        "domain": domain,
        "records": [
            {
                "type": "TXT",
                "name": domain,
                "purpose": "SPF",
                "value": f"v=spf1 include:_spf.{domain} ~all",
                "note": "Adjust 'include:' to match your SMTP provider.",
            },
            {
                "type": "TXT",
                "name": f"_dmarc.{domain}",
                "purpose": "DMARC",
                "value": f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain}",
                "note": "Start with p=none for monitoring, then move to quarantine/reject.",
            },
            {
                "type": "CNAME",
                "name": f"mail.{domain}",
                "purpose": "Mail subdomain",
                "value": "your-smtp-host.com",
                "note": "Point to your actual SMTP server.",
            },
            {
                "type": "MX",
                "name": domain,
                "purpose": "Mail exchange",
                "value": f"10 mail.{domain}",
                "note": "Priority 10. Add multiple MX records for redundancy.",
            },
        ],
        "message": f"DNS records guide for {domain}. "
                   f"Add these to your domain's DNS settings for better deliverability.",
    }
