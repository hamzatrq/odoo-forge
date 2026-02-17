# Changelog

All notable changes to OdooForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-02-18

### Added

- **Domain Knowledge Layer** — 5 MCP resources providing structured Odoo knowledge
  - `odoo://knowledge/modules` — 35 Odoo 18 modules mapped to business language
  - `odoo://knowledge/blueprints` — 9 industry blueprints (restaurant, ecommerce, manufacturing, services, retail, healthcare, education, nonprofit, professional)
  - `odoo://knowledge/dictionary` — business terms to Odoo model/field mapping
  - `odoo://knowledge/best-practices` — naming conventions, field design rules, security patterns
  - `odoo://knowledge/patterns` — common customization patterns (trackable models, approval workflows, partner extensions)
- **Planning Tools** (3 new tools)
  - `odoo_analyze_requirements` — parse natural language business descriptions into structured requirements
  - `odoo_design_solution` — generate phased implementation plans from analyzed requirements
  - `odoo_validate_plan` — validate plans against knowledge base rules and best practices
- **Workflow Tools** (4 new tools)
  - `odoo_setup_business` — generate complete business deployment step plans from blueprints
  - `odoo_create_feature` — generate custom feature creation step plans (fields, views, automations)
  - `odoo_create_dashboard` — generate dashboard creation step plans with metrics and menus
  - `odoo_setup_integration` — generate integration setup step plans (email, payment, shipping)
- **Code Generation** (1 new tool)
  - `odoo_generate_addon` — generate complete Odoo addon source code (manifest, models, views, security)
- **MCP Prompts** (4 guided workflows)
  - `business-setup` — full business deployment from natural language requirements
  - `feature-builder` — custom feature creation with validation
  - `module-generator` — complete addon scaffolding workflow
  - `troubleshooter` — systematic issue diagnosis and resolution
- **Claude Code Skills** (3 skills)
  - `odoo-brainstorm` — explore customization ideas, discover modules, match blueprints
  - `odoo-architect` — design data models with naming conventions, inheritance, and security
  - `odoo-debug` — diagnose issues with error mapping, log analysis, and snapshot rollback

### Changed

- Total tool count increased from 71 to **79 tools** across **20 categories**
- Test suite expanded from 212 to **545+ tests**
- Architecture expanded from single tool layer to 4-layer design:
  - Layer 0: Core Tools (71 tools — CRUD, modules, schema, views, etc.)
  - Layer 1: Domain Knowledge (5 resources — modules, blueprints, patterns)
  - Layer 2: Workflow Tools (4 tools — business setup, features, dashboards)
  - Layer 3: Planning Tools (3 tools — requirements, design, validation)

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
