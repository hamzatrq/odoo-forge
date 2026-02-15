# Changelog

All notable changes to OdooForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2024-02-16

### Added

- **71 MCP tools** across 16 categories for full Odoo 18 management
- **Instance management** — start, stop, restart, status, and log retrieval
- **Database management** — create, list, backup, restore, drop, and raw SQL
- **Record CRUD** — search, read, create, update, delete, and generic method execution
- **Snapshot system** — create, list, restore, and delete database snapshots
- **Module management** — list, info, install, upgrade, and uninstall modules
- **Model introspection** — list models, get fields, cross-model field search
- **Schema extension** — create/update/delete custom fields and models (x_ prefix)
- **View management** — list, get XML, modify via XPath inheritance, reset
- **QWeb reports** — list, get template, modify, preview, reset, layout config
- **Automation** — create/update/delete automated actions and email templates
- **Network tunneling** — expose Odoo via SSH or Cloudflare tunnels
- **CSV import** — preview, execute, and template generation
- **Email configuration** — SMTP/IMAP setup, test emails, DNS record guide
- **Settings & company** — system config, company details, user management
- **Knowledge base** — curated module info, search, and gap analysis
- **Industry recipes** — one-command setup for restaurant, ecommerce, manufacturing, services, retail
- **Diagnostics** — 7-point health check (Docker, DB, auth, modules, PG, logs, version)
- **Docker Compose** setup for Odoo 18 + PostgreSQL 17
- **Comprehensive test suite** — 212+ unit tests including edge cases
- **Full documentation** in `docs/` directory
