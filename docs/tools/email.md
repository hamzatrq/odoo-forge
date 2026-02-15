# Email Configuration Tools

Configure outgoing (SMTP) and incoming (IMAP/POP3) mail servers, send test emails, and generate DNS records for deliverability.

## `odoo_email_configure_outgoing`

Configure an outgoing SMTP mail server.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `name` | `str` | *required* | Server name (e.g., `"Company Gmail"`) |
| `smtp_host` | `str` | *required* | SMTP hostname (e.g., `"smtp.gmail.com"`) |
| `smtp_port` | `int` | `587` | SMTP port |
| `smtp_user` | `str` | `null` | SMTP username/email |
| `smtp_pass` | `str` | `null` | SMTP password or app password |
| `smtp_encryption` | `str` | `"starttls"` | Encryption: `"starttls"`, `"ssl"`, or `"none"` |
| `email_from` | `str` | `null` | Default sender address |

**Returns:** Server ID and creation/update status.

**Example:** `"Configure Gmail SMTP with host smtp.gmail.com, port 587, starttls encryption"`

---

## `odoo_email_configure_incoming`

Configure an incoming mail server (IMAP/POP3) for fetching emails.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `name` | `str` | *required* | Server name |
| `server_type` | `str` | `"imap"` | Protocol: `"imap"` or `"pop"` |
| `host` | `str` | `""` | Mail server hostname |
| `port` | `int` | `993` | Server port |
| `user` | `str` | `""` | Login username |
| `password` | `str` | `""` | Login password |
| `ssl` | `bool` | `true` | Use SSL/TLS |

**Returns:** Server ID and creation/update status.

---

## `odoo_email_test`

Send a test email to verify SMTP configuration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `to_address` | `str` | *required* | Recipient email address |
| `subject` | `str` | `"OdooForge Test Email"` | Email subject |
| `body` | `str` | `"This is a test email..."` | Email body |

**Returns:** Send status and any error details.

**Example:** `"Send a test email to admin@example.com"`

---

## `odoo_email_dns_guide`

Generate DNS records guide (SPF, DKIM, DMARC) for email deliverability.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain` | `str` | *required* | Email domain (e.g., `"acme.com"`) |

**Returns:** Recommended DNS records (SPF, DKIM, DMARC) with values.

**Example:** `"Generate DNS records for email deliverability on acme.com"`
