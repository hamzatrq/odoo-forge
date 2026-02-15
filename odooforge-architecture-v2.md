# OdooForge — AI-First ERP Configuration Engine

## Architecture & Development Blueprint v2 (Post-Audit)

---

## 1. EXECUTIVE SUMMARY

**OdooForge** is a CLI tool with an MCP (Model Context Protocol) layer that enables AI agents (Claude Code, Claude Desktop, Cursor, or any MCP-compatible client) to act as a **full-stack Odoo implementation consultant** — configuring, customizing, and maintaining a fresh Odoo instance from scratch through natural language conversation.

**Scope for v1:**
- Works with local Dockerized Odoo 18 Community instances
- Handles all built-in module installation, configuration, and data seeding
- Full CRUD on all Odoo models via XML-RPC
- **No-code UI customization** (view inheritance via XPath, stored in `ir.ui.view`)
- **Business automation** (automated actions via `base.automation` and `ir.actions.server`)
- **Batch data import** (CSV/JSON bulk loading via Odoo's native `load()` method)
- **Snapshot/rollback** for safe experimentation
- Infrastructure management (restart, logs, database operations)
- **OCA module awareness** (knowledge base covers key Community Association modules for gaps like accounting reports)
- Email/SMTP configuration workflows
- Does NOT create custom Python file-based modules (planned for v2)
- Contains comprehensive knowledge of all Odoo Community modules + key OCA modules

**Key Insight from Research:** Several Odoo MCP servers exist (tuanle96/mcp-odoo, vzeman/odoo-mcp-server, Odoo Apps Store MCP modules), but they are all **data-layer only** — they let AI query and manipulate existing records. None of them handle the full lifecycle: infrastructure, module installation, UI customization, automation rules, data migration, or carry embedded implementation knowledge. OdooForge fills that gap by being an **AI implementation consultant**, not just an API wrapper.

**Design Philosophy — Three Roles:**
The AI agent using OdooForge operates as three personas simultaneously:
1. **DevOps Engineer** — Infrastructure, Docker, database management
2. **Implementation Consultant** — Module selection, configuration, workflow design
3. **No-Code Developer** — View customization, automation rules, report configuration

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                       AI CLIENT LAYER                            │
│      (Claude Code / Claude Desktop / Cursor / Custom)            │
└────────────────────────────┬────────────────────────────────────┘
                             │ MCP Protocol (stdio / streamable-http)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    ODOOFORGE MCP SERVER                           │
│                                                                   │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────────┐   │
│  │  Instance    │ │   Module     │ │  No-Code Customization  │   │
│  │  Manager     │ │   Manager    │ │  Layer                  │   │
│  │  (Docker +   │ │  (Install/   │ │  • View/XPath modifier  │   │
│  │   Snapshots) │ │   Configure) │ │  • Automation engine    │   │
│  │              │ │              │ │  • Email configuration  │   │
│  └──────┬──────┘ └──────┬──────┘ └───────────┬─────────────┘   │
│         │               │                     │                   │
│  ┌──────┴───────┐ ┌─────┴──────┐ ┌───────────┴─────────────┐   │
│  │  Data        │ │  Import    │ │  Diagnostics &           │   │
│  │  Manager     │ │  Engine    │ │  Verification            │   │
│  │  (CRUD on    │ │  (Batch    │ │  • Post-install verify   │   │
│  │   all models)│ │   CSV/JSON)│ │  • Field existence check │   │
│  │              │ │            │ │  • View integrity check  │   │
│  └──────┬──────┘ └─────┬──────┘ └───────────┬─────────────┘   │
│         │               │                     │                   │
│  ┌──────▼───────────────▼─────────────────────▼─────────────┐   │
│  │              ODOO CONNECTION LAYER                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────┐             │   │
│  │  │ XML-RPC  │  │  Docker  │  │  PostgreSQL  │             │   │
│  │  │ Client   │  │  Client  │  │  Client      │             │   │
│  │  └──────────┘  └──────────┘  └─────────────┘             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          KNOWLEDGE BASE (Read-Only + Live Refresh)        │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │   │
│  │  │ Module   │ │ OCA      │ │ Config   │ │ Live State │  │   │
│  │  │ Catalog  │ │ Registry │ │ Recipes  │ │ Cache      │  │   │
│  │  │ (static) │ │ (static) │ │ (static) │ │ (dynamic)  │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
               ┌─────────────▼─────────────┐
               │   LOCAL ODOO INSTANCE       │
               │  ┌────────┐ ┌────────┐     │
               │  │ Odoo18 │ │Postgres│     │
               │  │  :8069  │ │ :5432  │     │
               │  └────────┘ └────────┘     │
               │     Docker Compose          │
               └────────────────────────────┘
```

### Critical Architectural Addition: The Verification Loop

Every mutating operation follows this pattern:

```
  Action (install/configure/modify)
         │
         ▼
  Verify against live instance
  (fields_get, search_read, view render check)
         │
         ▼
  Update Live State Cache
  (so AI always has current truth)
         │
         ▼
  Return result + current state to AI
```

The AI must never trust its static knowledge once the instance is live. The **Live State Cache** is refreshed after every mutation and provides the ground truth for subsequent operations.

---

## 3. WHAT EXISTS vs WHAT WE BUILD

### 3.1 Existing Tools (Research Findings)

| Tool | What It Does | Limitation |
|---|---|---|
| **tuanle96/mcp-odoo** | XML-RPC MCP with `execute_method`, `search_employee`, resource URIs | Only 3 hardcoded tools + generic execute. No module install, no infrastructure |
| **vzeman/odoo-mcp-server** | Docker-based, HTTP+stdio, `search_records`, `create_record` | Data CRUD only. No module management, no Docker control |
| **Odoo Apps Store MCP** | Odoo module that exposes MCP from within Odoo | Requires manual setup. No external control. Enterprise-focused |
| **CData MCP for Odoo** | Commercial connector for querying data | Read-only analytics. Paid |

### 3.2 What OdooForge Adds (Complete Gap Coverage)

| Capability | Existing MCP Servers | OdooForge |
|---|---|---|
| Record CRUD | ✅ | ✅ |
| Infrastructure (Docker) | ❌ | ✅ |
| Module Lifecycle | ❌ | ✅ |
| Database Management | ❌ | ✅ |
| **View/UI Customization (XPath)** | ❌ | ✅ |
| **Automation Rules** | ❌ | ✅ |
| **Batch Data Import** | ❌ | ✅ |
| **Snapshot/Rollback** | ❌ | ✅ |
| **Email/SMTP Configuration** | ❌ | ✅ |
| **OCA Module Awareness** | ❌ | ✅ |
| **Implementation Knowledge Base** | ❌ | ✅ |
| **Live State Verification** | ❌ | ✅ |
| Configuration Recipes | ❌ | ✅ |
| Diagnostics & Logs | ❌ | ✅ |

---

## 4. PROJECT STRUCTURE

```
odooforge/
├── pyproject.toml                  # Package config, deps, entry points
├── README.md
├── LICENSE
├── docker/
│   ├── docker-compose.yml          # Odoo 18 + PostgreSQL 17
│   ├── odoo.conf                   # Odoo server config
│   └── addons/                     # Mount point for future custom modules (v2)
│
├── src/
│   └── odooforge/
│       ├── __init__.py
│       ├── server.py               # MCP server entry point (FastMCP)
│       ├── config.py               # Environment/config management
│       │
│       ├── connections/
│       │   ├── __init__.py
│       │   ├── xmlrpc_client.py    # Odoo XML-RPC wrapper
│       │   ├── docker_client.py    # Docker/docker-compose operations
│       │   └── pg_client.py        # Direct PostgreSQL access
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── instance.py         # Instance lifecycle tools
│       │   ├── database.py         # Database management tools
│       │   ├── snapshots.py        # Snapshot/rollback tools (NEW)
│       │   ├── modules.py          # Module install/upgrade/uninstall
│       │   ├── models.py           # Introspection (list models, fields)
│       │   ├── records.py          # CRUD on any model
│       │   ├── import_engine.py    # Batch CSV/JSON import (NEW)
│       │   ├── views.py            # View/XPath customization (NEW)
│       │   ├── automation.py       # Automated actions & server actions (NEW)
│       │   ├── email_config.py     # Mail server setup (NEW)
│       │   ├── settings.py         # System settings & configuration
│       │   ├── users.py            # User/access management
│       │   ├── diagnostics.py      # Logs, health checks, SQL
│       │   └── recipes.py          # Pre-built configuration workflows
│       │
│       ├── verification/           # (NEW) Post-action verification layer
│       │   ├── __init__.py
│       │   ├── state_cache.py      # Live state cache management
│       │   ├── verify_install.py   # Post-install module/field verification
│       │   ├── verify_view.py      # View integrity checking
│       │   └── verify_automation.py # Automation rule validation
│       │
│       ├── knowledge/
│       │   ├── __init__.py
│       │   ├── module_catalog.py   # All Community modules metadata
│       │   ├── oca_registry.py     # Key OCA modules for Community gaps (NEW)
│       │   ├── model_registry.py   # Key models per module
│       │   ├── config_patterns.py  # Common configuration patterns
│       │   └── data/
│       │       ├── modules.json    # Module catalog data
│       │       ├── oca_modules.json # OCA module catalog (NEW)
│       │       ├── models.json     # Model-to-module mapping
│       │       ├── settings.json   # Settings reference
│       │       ├── community_gaps.json # Known CE limitations + fixes (NEW)
│       │       └── recipes/
│       │           ├── restaurant.json
│       │           ├── ecommerce.json
│       │           ├── manufacturing.json
│       │           ├── services.json
│       │           └── email_setup.json    # (NEW)
│       │
│       └── utils/
│           ├── __init__.py
│           ├── formatting.py       # Response formatting (MD/JSON)
│           ├── validators.py       # Common validation logic
│           ├── xpath_builder.py    # XPath expression generator (NEW)
│           └── errors.py           # Error handling helpers
│
└── tests/
    ├── test_xmlrpc.py
    ├── test_docker.py
    ├── test_modules.py
    ├── test_records.py
    ├── test_views.py              # (NEW)
    ├── test_automation.py         # (NEW)
    ├── test_import.py             # (NEW)
    └── test_snapshots.py          # (NEW)
```

---

## 5. COMPLETE TOOL SPECIFICATION

### 5.1 Instance Management Tools

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_instance_start                                        │
│ Starts the Odoo Docker environment (Odoo + PostgreSQL)           │
│ Params: config_path? (optional), port? (default 8069)            │
│ Returns: Status, URL, container IDs                              │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_instance_stop                                         │
│ Stops the running Odoo Docker environment                        │
│ Params: remove_volumes? (bool, default false)                    │
│ Returns: Status                                                  │
│ Annotations: readOnly=false, destructive=true                    │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_instance_restart                                      │
│ Restarts the Odoo service (not PostgreSQL)                       │
│ Params: none                                                     │
│ Returns: Status, uptime                                          │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_instance_status                                       │
│ Returns health status of all containers                          │
│ Params: none                                                     │
│ Returns: Container states, ports, resource usage, Odoo version   │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_instance_logs                                         │
│ Retrieves Odoo server logs                                       │
│ Params: lines? (default 100), level_filter?, since?, grep?       │
│ Returns: Log lines (filtered)                                    │
│ Annotations: readOnly=true                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Database Management Tools

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_db_create                                             │
│ Creates a new Odoo database and initializes base module          │
│ Params: db_name, admin_password, language?, country?,             │
│         demo_data? (bool)                                        │
│ Returns: Status, database info                                   │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_db_list                                               │
│ Lists all databases on the instance                              │
│ Params: none                                                     │
│ Returns: List of database names and sizes                        │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_db_backup                                             │
│ Creates a backup of a database                                   │
│ Params: db_name, format? (zip/dump, default zip)                 │
│ Returns: Backup file path, size                                  │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_db_restore                                            │
│ Restores a database from backup                                  │
│ Params: db_name, backup_path, overwrite? (bool)                  │
│ Returns: Status                                                  │
│ Annotations: readOnly=false, destructive=true                    │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_db_drop                                               │
│ Drops a database permanently                                     │
│ Params: db_name, confirm (must be true)                          │
│ Returns: Status                                                  │
│ Annotations: readOnly=false, destructive=true                    │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_db_run_sql                                            │
│ Executes a raw SQL query against the database                    │
│ Params: db_name, query, params?                                  │
│ Returns: Query results (rows, columns, row_count)                │
│ Annotations: readOnly=false, destructive=true                    │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Snapshot & Rollback Tools (NEW — Audit Item)

These are essential for safe AI-driven experimentation. Before the AI modifies views or automation rules, it creates a snapshot. If something breaks the web UI (a bad XPath → 500 error), the AI can roll back.

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_snapshot_create                                       │
│ Creates a named database snapshot (pg_dump + metadata)           │
│ Params: db_name, snapshot_name, description?                     │
│ Returns: Snapshot ID, path, size, timestamp                      │
│ Notes: Auto-called before destructive operations if the AI       │
│        sets auto_snapshot=true. Stored locally with metadata.    │
│ Annotations: readOnly=true, destructive=false                    │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_snapshot_list                                         │
│ Lists all available snapshots for a database                     │
│ Params: db_name                                                  │
│ Returns: List of snapshots with name, timestamp, size, desc      │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_snapshot_restore                                      │
│ Restores a database to a previous snapshot                       │
│ Params: db_name, snapshot_name, confirm (must be true)           │
│ Returns: Status, restored timestamp                              │
│ Notes: Drops current DB, restores from snapshot, restarts Odoo.  │
│        Creates an auto-snapshot of current state before restore. │
│ Annotations: readOnly=false, destructive=true                    │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_snapshot_delete                                       │
│ Deletes a snapshot to free disk space                            │
│ Params: snapshot_name, confirm (must be true)                    │
│ Returns: Status, freed space                                     │
│ Annotations: readOnly=false, destructive=true                    │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation Detail:** Snapshots use `pg_dump` via Docker exec into the PostgreSQL container. Metadata (name, description, timestamp, list of installed modules at time of snapshot) is stored in a local JSON manifest alongside the dump file. This is faster and more reliable than Odoo's built-in backup for rollback purposes.

### 5.4 Module Management Tools

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_module_list_available                                 │
│ Lists all available (installable) modules                        │
│ Params: db_name, category_filter?, search_term?                  │
│ Returns: Module list with name, tech_name, state, summary        │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_module_list_installed                                 │
│ Lists currently installed modules                                │
│ Params: db_name                                                  │
│ Returns: Installed module list with versions                     │
│ Post-action: Updates Live State Cache                            │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_module_info                                           │
│ Gets detailed info about a specific module (from live instance)  │
│ Params: db_name, module_name                                     │
│ Returns: Description, dependencies, state, models it provides,   │
│          settings keys, views registered                         │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_module_install                                        │
│ Installs one or more modules                                     │
│ Params: db_name, modules (list of tech names),                   │
│         auto_snapshot? (bool, default true)                      │
│ Returns: Status, installed modules (including auto-dependencies),│
│          new models now available, new settings unlocked         │
│ Post-action: Runs verification → refreshes Live State Cache      │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_module_upgrade                                        │
│ Upgrades one or more installed modules                           │
│ Params: db_name, modules (list or "all")                         │
│ Returns: Status, upgraded modules                                │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_module_uninstall                                      │
│ Uninstalls a module (with dependency check)                      │
│ Params: db_name, module_name, force? (bool)                      │
│ Returns: Status, affected/removed modules                        │
│ Annotations: readOnly=false, destructive=true                    │
└─────────────────────────────────────────────────────────────────┘
```

**Critical Pattern — Post-Install Verification:**
After every `odoo_module_install`, the tool internally:
1. Checks Odoo logs for errors (no traceback/500s)
2. Calls `fields_get()` on the new models the module is expected to provide
3. Verifies the module state is "installed" in `ir.module.module`
4. Updates the Live State Cache with new models, fields, and settings
5. Returns the verification result alongside the install status

This prevents the AI from assuming a field exists when the install silently failed.

### 5.5 Model Introspection Tools

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_model_list                                            │
│ Lists all models in the system                                   │
│ Params: db_name, search_term?, module_filter?                    │
│ Returns: List of models with names, descriptions, module source  │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_model_fields                                          │
│ Gets all fields for a specific model                             │
│ Params: db_name, model_name, include_inherited? (bool)           │
│ Returns: Field list with types, required, readonly, relations,   │
│          selection values, help text, module that added it       │
│ Notes: This is the AI's "source of truth" for what fields exist. │
│        The AI MUST call this before attempting to write/create    │
│        records on an unfamiliar model.                           │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_model_search_field                                    │
│ Finds which model(s) contain a field matching a search term      │
│ Params: db_name, field_search (e.g., "email", "tax", "price")   │
│ Returns: List of (model, field_name, field_type, label)          │
│ Notes: Useful when AI needs to find "where is tax configured?"   │
│ Annotations: readOnly=true                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 5.6 Record CRUD Tools

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_record_search                                         │
│ Search for records in any model                                  │
│ Params: db_name, model, domain, fields?, limit? (default 20),   │
│         offset?, order?                                          │
│ Returns: Records matching criteria with pagination info          │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_record_read                                           │
│ Read specific records by ID                                      │
│ Params: db_name, model, ids (list), fields?                      │
│ Returns: Record data                                             │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_record_create                                         │
│ Create one or more records                                       │
│ Params: db_name, model, values (dict or list of dicts)           │
│ Returns: Created record IDs                                      │
│ Pre-action: Validates field names against live fields_get()      │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_record_update                                         │
│ Update existing records                                          │
│ Params: db_name, model, ids, values                              │
│ Returns: Status, updated count                                   │
│ Pre-action: Validates field names against live fields_get()      │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_record_delete                                         │
│ Delete records                                                   │
│ Params: db_name, model, ids, confirm (must be true)              │
│ Returns: Status, deleted count                                   │
│ Annotations: readOnly=false, destructive=true                    │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_record_execute                                        │
│ Execute any method on any model (generic escape hatch)           │
│ Params: db_name, model, method, args?, kwargs?                   │
│ Returns: Method result                                           │
│ Annotations: readOnly=false, destructive=false                   │
└─────────────────────────────────────────────────────────────────┘
```

### 5.7 Batch Data Import Tools (NEW — Audit Item)

Addresses the "5,000 customers in CSV" problem. Using `odoo_record_create` in a loop through the LLM is wasteful (thousands of tool calls, each consuming tokens). Instead, the batch import tool accepts a data payload and uses Odoo's native `load()` method, which handles relational field resolution, deduplication, and error reporting natively.

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_import_preview                                        │
│ Previews an import without executing it                          │
│ Params: db_name, model, data (CSV string or JSON array),         │
│         field_mapping? (dict: column→odoo_field),                │
│         has_header? (bool, default true)                         │
│ Returns: Parsed row count, detected columns, auto-mapped fields, │
│          unmapped columns requiring manual mapping, sample rows,  │
│          potential issues (type mismatches, missing required)     │
│ Notes: The AI uses this to understand the data shape before       │
│        committing. No records are created.                       │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_import_execute                                        │
│ Executes a batch import using Odoo's native load() method        │
│ Params: db_name, model, data (CSV string or JSON array),         │
│         field_mapping (dict: column→odoo_field),                 │
│         on_error? ("skip" | "abort", default "skip"),            │
│         auto_snapshot? (bool, default true)                      │
│ Returns: imported_count, skipped_count, error_rows (with         │
│          row number and error message for each failure),          │
│          created_ids (list of new record IDs)                    │
│ Notes: Uses Odoo's `load()` which supports:                      │
│        - Relational field resolution via name_search             │
│        - External ID (XML ID) references                        │
│        - Many2one by name: "country_id" → "Pakistan" resolves   │
│        - One2many/Many2many via special `/` syntax               │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_import_template                                       │
│ Generates an import template for a model                         │
│ Params: db_name, model, include_optional? (bool)                 │
│ Returns: CSV header row with correct Odoo field names,           │
│          field type hints, example values, required flags         │
│ Notes: Helps the AI understand what data shape Odoo expects.     │
│ Annotations: readOnly=true                                       │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation Detail — `load()` method:**
Odoo's `load()` is significantly better than `create()` for bulk operations because:
- It resolves Many2one fields by name (e.g., `country_id` = "Pakistan" → finds `res.country` record)
- It handles external ID references (`id` column for XML IDs)
- It returns per-row error details instead of failing the whole batch
- It's the same method the Odoo web UI's "Import" feature uses internally

```python
# How it works internally
result = models.execute_kw(
    db, uid, password,
    'res.partner', 'load',
    [['name', 'email', 'country_id', 'phone'],  # field names
     [                                             # data rows
         ['Steamin', 'info@steamin.pk', 'Pakistan', '+92-300-1234567'],
         ['Customer 2', 'c2@example.com', 'Pakistan', '+92-321-9876543'],
     ]],
    {}
)
# result = {'ids': [45, 46], 'messages': []}
```

### 5.8 View & UI Customization Tools (NEW — Audit Item: Critical)

This is the **most important audit finding**. In Odoo, UI modifications are data records in `ir.ui.view`, not Python code. The AI can customize any form, tree, kanban, or search view by creating inheriting views with XPath expressions — all via XML-RPC.

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_view_list                                             │
│ Lists all views for a model (form, tree, kanban, search, etc.)  │
│ Params: db_name, model, view_type? (form/tree/kanban/search)     │
│ Returns: List of views with id, name, type, inherit_id,         │
│          priority, active status, module source                  │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_view_get_arch                                         │
│ Gets the full XML architecture of a specific view                │
│ Params: db_name, model, view_type? (default "form"),             │
│         view_id? (specific view)                                 │
│ Returns: The complete rendered/compiled XML arch of the view,    │
│          with field names highlighted for easy XPath targeting.   │
│          Also returns a "field inventory" — list of all field    │
│          names present in the view with their current attributes.│
│ Notes: The AI MUST call this before modifying a view, to         │
│        understand the current layout and find correct XPath      │
│        targets. This returns the COMPILED view (all inherited    │
│        views merged), which is what the user actually sees.      │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_view_modify                                           │
│ Creates an inherited view that modifies the UI                   │
│ Params: db_name, model, view_type, modifications (list of:       │
│         {                                                        │
│           action: "hide" | "show" | "rename" | "move" |         │
│                   "add_field" | "remove" | "set_attribute",      │
│           target: field_name or xpath_expr,                      │
│           value: (new label / attribute value / position),       │
│           position?: "before" | "after" | "inside" | "replace"  │
│         }),                                                      │
│         auto_snapshot? (bool, default true)                      │
│ Returns: Created view ID, name, applied modifications            │
│                                                                  │
│ INTERNAL: The tool translates high-level actions into XPath:     │
│                                                                  │
│ "hide tax_id on customer form" becomes:                          │
│   <xpath expr="//field[@name='vat']" position="attributes">     │
│     <attribute name="invisible">1</attribute>                    │
│   </xpath>                                                       │
│                                                                  │
│ "rename 'Street' to 'Address Line 1'" becomes:                  │
│   <xpath expr="//field[@name='street']" position="attributes">  │
│     <attribute name="string">Address Line 1</attribute>          │
│   </xpath>                                                       │
│                                                                  │
│ "add field 'x_loyalty_points' after 'email'" becomes:           │
│   <xpath expr="//field[@name='email']" position="after">        │
│     <field name="x_loyalty_points"/>                             │
│   </xpath>                                                       │
│                                                                  │
│ Post-action: Verifies view renders without error (test GET on    │
│              the form URL), logs the XPath for rollback           │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_view_reset                                            │
│ Removes a specific customization (deletes the inherited view)    │
│ Params: db_name, view_id (the customization view ID)             │
│ Returns: Status                                                  │
│ Annotations: readOnly=false, destructive=true                    │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_view_list_customizations                              │
│ Lists all view customizations created by OdooForge               │
│ Params: db_name, model?                                          │
│ Returns: List of custom inherited views with their modifications │
│ Notes: Only shows views with a specific naming convention         │
│        (e.g., prefix "odooforge_") so we don't touch system ones │
│ Annotations: readOnly=true                                       │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation Detail — View Modification:**
```python
# Creating an inherited view via XML-RPC
# This hides the "Tax ID" field from the partner form

parent_view = models.execute_kw(db, uid, password,
    'ir.ui.view', 'search_read',
    [[['model', '=', 'res.partner'], ['type', '=', 'form'],
      ['inherit_id', '=', False]]],  # Get the root form view
    {'fields': ['id', 'name'], 'limit': 1}
)

# Create the inheriting view
view_id = models.execute_kw(db, uid, password,
    'ir.ui.view', 'create',
    [{
        'name': 'odooforge_partner_form_hide_vat',
        'model': 'res.partner',
        'inherit_id': parent_view[0]['id'],
        'arch': '''
            <xpath expr="//field[@name='vat']" position="attributes">
                <attribute name="invisible">1</attribute>
            </xpath>
        ''',
        'priority': 99,  # Higher = applied later
    }]
)
```

**XPath Builder Utility (`utils/xpath_builder.py`):**
The AI doesn't need to write raw XPath. The tool accepts high-level actions and the `xpath_builder` translates them:

```python
def build_xpath(action: str, target: str, value: str = None) -> str:
    """
    Translates high-level view modification requests into XPath XML.

    action="hide", target="vat"
    → <xpath expr="//field[@name='vat']" position="attributes">
          <attribute name="invisible">1</attribute>
      </xpath>

    action="rename", target="street", value="Address Line 1"
    → <xpath expr="//field[@name='street']" position="attributes">
          <attribute name="string">Address Line 1</attribute>
      </xpath>

    action="add_field", target="email", value="x_loyalty_points",
           position="after"
    → <xpath expr="//field[@name='email']" position="after">
          <field name="x_loyalty_points"/>
      </xpath>

    action="remove", target="website"
    → <xpath expr="//field[@name='website']" position="replace"/>
    """
```

### 5.9 Automation Tools (NEW — Audit Item)

Exposes Odoo's no-code automation engine: `base.automation` (automated actions) and `ir.actions.server` (server actions). This lets the AI create "When X happens, do Y" rules without Python code.

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_automation_list                                       │
│ Lists all existing automated actions                             │
│ Params: db_name, model_filter?                                   │
│ Returns: List of automations with trigger, model, action, active │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_automation_create                                     │
│ Creates an automated action (no-code "if/then" rule)             │
│ Params: db_name,                                                 │
│   name: str (human-readable name),                               │
│   model: str (e.g., "sale.order"),                               │
│   trigger: "on_create" | "on_write" | "on_unlink" |             │
│            "on_create_or_write" | "on_time",                     │
│   trigger_fields?: list (for on_write: which fields trigger it), │
│   domain_filter?: list (Odoo domain to filter records),          │
│   actions: list of {                                             │
│     type: "update_record" | "create_record" | "send_email" |    │
│           "add_followers" | "create_activity" |                  │
│           "send_sms" | "execute_code",                           │
│     params: dict (type-specific parameters)                      │
│   }                                                              │
│                                                                  │
│ SCENARIO EXAMPLES:                                               │
│                                                                  │
│ "Flag large orders for review":                                  │
│   model="sale.order", trigger="on_create_or_write",              │
│   trigger_fields=["amount_total"],                               │
│   domain=[["amount_total", ">", 500000]],                       │
│   actions=[{type: "update_record",                               │
│             params: {values: {"priority": "1"}}}]                │
│                                                                  │
│ "Email manager when order confirmed":                            │
│   model="sale.order", trigger="on_write",                        │
│   trigger_fields=["state"],                                      │
│   domain=[["state", "=", "sale"]],                               │
│   actions=[{type: "send_email",                                  │
│             params: {template_ref: "...", partner_to: "..."}}]   │
│                                                                  │
│ "Auto-assign sales team based on country":                       │
│   model="crm.lead", trigger="on_create",                        │
│   actions=[{type: "execute_code",                                │
│             params: {code: "record.team_id = ..."}}]             │
│                                                                  │
│ Returns: Automation ID, summary of what was created              │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_automation_update                                     │
│ Modifies an existing automation (e.g., change domain, disable)   │
│ Params: db_name, automation_id, changes (dict)                   │
│ Returns: Status                                                  │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_automation_delete                                     │
│ Deletes an automation rule                                       │
│ Params: db_name, automation_id, confirm (must be true)           │
│ Returns: Status                                                  │
│ Annotations: readOnly=false, destructive=true                    │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_email_template_create                                 │
│ Creates an email template for use in automations                 │
│ Params: db_name, name, model, subject (with placeholders),       │
│         body_html (with Jinja-like Odoo placeholders),           │
│         email_from?, partner_to?, auto_delete?                   │
│ Returns: Template ID                                             │
│ Notes: Supports Odoo's QWeb placeholder syntax:                  │
│        {{ object.partner_id.name }}, {{ object.amount_total }}   │
│ Annotations: readOnly=false, destructive=false                   │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation Detail — `base.automation` record structure:**
```python
automation_id = models.execute_kw(db, uid, password,
    'base.automation', 'create',
    [{
        'name': 'Flag Large Orders for Review',
        'model_id': sale_order_model_id,    # ir.model ID for sale.order
        'trigger': 'on_create_or_write',
        'trigger_field_ids': [(6, 0, [amount_total_field_id])],
        'filter_domain': "[('amount_total', '>', 500000)]",
        'action_server_ids': [(6, 0, [server_action_id])],
        'active': True,
    }]
)
```

### 5.10 Email & Communication Configuration (NEW — Audit Item)

Email setup is the #1 post-installation hurdle. The AI needs specialized tooling to handle SMTP/IMAP configuration, test connectivity, and guide DNS setup.

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_email_configure_outgoing                              │
│ Configures outgoing mail server (SMTP)                           │
│ Params: db_name, name, smtp_host, smtp_port,                     │
│         smtp_encryption ("none"|"starttls"|"ssl"),               │
│         smtp_user, smtp_pass,                                    │
│         from_filter?                                             │
│ Returns: Server ID, test email result (sends test to admin)      │
│ Post-action: Automatically sends a test email to verify config.  │
│   Returns clear error if it fails (wrong password, blocked port, │
│   SSL mismatch, etc.)                                            │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_email_configure_incoming                              │
│ Configures incoming mail server (IMAP/POP3)                      │
│ Params: db_name, name, server_type ("imap"|"pop"),               │
│         server_host, server_port, ssl, user, password,           │
│         action_on_email? ("create_lead"|"create_ticket"|none)    │
│ Returns: Server ID, test fetch result                            │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_email_test                                            │
│ Tests current email configuration by sending a test email        │
│ Params: db_name, recipient_email                                 │
│ Returns: Success/failure with detailed error message             │
│ Annotations: readOnly=true, destructive=false                    │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_email_dns_guide                                       │
│ Generates DNS configuration instructions for the user's domain   │
│ Params: domain (e.g., "steamin.pk"), provider?                   │
│ Returns: Required DNS records:                                   │
│   - SPF record (TXT)                                             │
│   - DKIM record (if available)                                   │
│   - DMARC record (recommended)                                   │
│   - MX records (if using Odoo for incoming)                      │
│ Notes: This is a knowledge-based tool (no API call). It          │
│   generates the DNS records the user needs to add at their       │
│   domain registrar. The AI can explain each record's purpose.    │
│ Annotations: readOnly=true                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 5.11 Settings & Configuration Tools

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_settings_get                                          │
│ Reads current system settings (res.config.settings)              │
│ Params: db_name, category? (general|sales|inventory|accounting   │
│         |purchase|hr|pos|website|project)                        │
│ Returns: Current settings values, grouped by category            │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_settings_set                                          │
│ Updates system settings                                          │
│ Params: db_name, settings (dict of key-value pairs)              │
│ Returns: Status, applied settings, any side effects              │
│ Notes: Settings in Odoo are transactional — they're written to   │
│   res.config.settings, then "executed". This tool handles both.  │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_company_configure                                     │
│ Configures the main company details                              │
│ Params: db_name, name?, address?, city?, state?, country?,       │
│         currency?, vat?, logo_base64?, phone?, email?, website?  │
│ Returns: Status, company record                                  │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_users_manage                                          │
│ Create/update users and assign access groups                     │
│ Params: db_name, action ("create"|"update"|"deactivate"),        │
│         user_data (name, login, email, password),                │
│         groups? (list of group XML IDs)                          │
│ Returns: User info, assigned permissions                         │
│ Annotations: readOnly=false, destructive=false                   │
└─────────────────────────────────────────────────────────────────┘
```

### 5.12 Knowledge & Recipe Tools

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_knowledge_module_info                                 │
│ Returns knowledge about an Odoo module from embedded knowledge   │
│ base (NOT from live instance — use odoo_module_info for that)    │
│ Params: module_name                                              │
│ Returns: Purpose, key models, settings, best practices,          │
│          configuration patterns, dependencies, known limitations, │
│          OCA alternatives (if Community gaps exist)               │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_knowledge_search                                      │
│ Searches the knowledge base for how to achieve something         │
│ Params: query (e.g., "track inventory by lot number",            │
│         "set up Pakistani tax GST", "generate balance sheet")    │
│ Returns: Relevant modules, settings, configuration steps,        │
│          OCA modules if needed, known Community limitations       │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_knowledge_community_gaps                              │
│ Lists known Odoo Community limitations and recommended fixes     │
│ Params: area? (accounting|hr|reporting|manufacturing)            │
│ Returns: Gap description, impact, recommended OCA module or      │
│          workaround                                              │
│ Example gaps:                                                    │
│   - "No dynamic Balance Sheet/P&L" → OCA account_financial_report│
│   - "No payroll" → OCA payroll modules                           │
│   - "No document management" → OCA DMS                           │
│   - "No advanced recurring invoices" → workarounds               │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_recipe_list                                           │
│ Lists available pre-built configuration recipes                  │
│ Params: industry_filter?                                         │
│ Returns: Recipe list with descriptions                           │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_recipe_execute                                        │
│ Executes a configuration recipe (multi-step workflow)            │
│ Params: db_name, recipe_name, customizations? (dict)             │
│ Returns: Step-by-step execution log with status per step,        │
│          snapshot_name (auto-created before execution)            │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_diagnostics_health_check                              │
│ Runs a comprehensive health check on the instance                │
│ Params: db_name                                                  │
│ Returns: Module install status, broken views, failed automations,│
│          email delivery status, database size, orphaned records  │
│ Annotations: readOnly=true                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. CONNECTION LAYER DESIGN

### 6.1 XML-RPC Client (`connections/xmlrpc_client.py`)

Primary interface for all Odoo data operations.

```python
class OdooRPC:
    """Thread-safe XML-RPC wrapper for Odoo with session caching."""

    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url
        self.db = db
        self.uid: int | None = None
        self._common = ServerProxy(f"{url}/xmlrpc/2/common")
        self._object = ServerProxy(f"{url}/xmlrpc/2/object")

    def authenticate(self) -> int:
        """Authenticate and cache uid. Raises on failure."""

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """Generic execute_kw wrapper with error handling."""

    def search_read(self, model, domain, fields=None, limit=20, offset=0, order=None):
        """Convenience: search + read in one call."""

    def create(self, model: str, values: dict | list[dict]) -> int | list[int]:
        """Create record(s). Validates field names first."""

    def write(self, model: str, ids: list[int], values: dict) -> bool:
        """Update record(s)."""

    def unlink(self, model: str, ids: list[int]) -> bool:
        """Delete record(s)."""

    def fields_get(self, model: str, attributes: list[str] | None = None) -> dict:
        """Introspect model fields. Core truth source."""

    def load(self, model: str, fields: list[str], data: list[list]) -> dict:
        """Bulk import using Odoo's native load(). Returns {ids, messages}."""

    def execute_method(self, model: str, method: str, args=None, kwargs=None) -> Any:
        """Call any model method."""

    # --- View-specific helpers ---
    def get_view(self, model: str, view_type: str = 'form', view_id: int = None) -> dict:
        """Get compiled view arch via get_view() or fields_view_get()."""

    def create_inheriting_view(self, model: str, parent_view_id: int,
                                name: str, arch: str, priority: int = 99) -> int:
        """Create a new ir.ui.view record that inherits from parent."""
```

**Design decisions:**
- XML-RPC for Odoo 17/18 compatibility (JSON-2 API adapter planned for Odoo 19+)
- `load()` exposed directly for batch import — this is the key differentiator vs `create()` loops
- View-specific helpers because `ir.ui.view` operations are complex enough to warrant dedicated methods
- All methods include retry logic with exponential backoff

### 6.2 Docker Client (`connections/docker_client.py`)

```python
class OdooDocker:
    """Docker Compose wrapper for Odoo infrastructure management."""

    def __init__(self, compose_path: str):
        self.compose_path = compose_path
        self._snapshots_dir = Path(compose_path) / "snapshots"

    async def up(self, detach: bool = True) -> dict:
        """docker compose up -d"""

    async def down(self, remove_volumes: bool = False) -> dict:
        """docker compose down [-v]"""

    async def restart_service(self, service: str = "web") -> dict:
        """docker compose restart web"""

    async def logs(self, service="web", lines=100, since=None, grep=None) -> str:
        """docker compose logs --tail={lines} [--since=...]"""

    async def exec_in_container(self, service: str, command: str) -> str:
        """docker compose exec {service} {command}"""

    async def status(self) -> dict:
        """Container states, ports, health, resource usage."""

    # Module installation via Odoo CLI (more reliable than XML-RPC)
    async def install_module_via_cli(self, db: str, modules: list[str]) -> str:
        """docker compose exec web odoo -d {db} -i {','.join(modules)} --stop-after-init"""

    async def upgrade_module_via_cli(self, db: str, modules: list[str]) -> str:
        """docker compose exec web odoo -d {db} -u {','.join(modules)} --stop-after-init"""

    # Snapshot operations (via pg_dump/pg_restore in the db container)
    async def create_snapshot(self, db: str, name: str) -> dict:
        """pg_dump via docker exec into postgres container."""

    async def restore_snapshot(self, db: str, name: str) -> dict:
        """Drop db, pg_restore, restart Odoo."""

    async def list_snapshots(self, db: str) -> list[dict]:
        """Read snapshot manifests from snapshots directory."""
```

### 6.3 PostgreSQL Client (`connections/pg_client.py`)

```python
class OdooPG:
    """Direct PostgreSQL access for diagnostics and operations."""

    def __init__(self, host, port, user, password, db):
        self.dsn = f"postgresql://{user}:{password}@{host}:{port}/{db}"

    async def query(self, sql: str, params=None) -> list[dict]:
        """Execute SELECT query, return rows as dicts."""

    async def execute(self, sql: str, params=None) -> int:
        """Execute INSERT/UPDATE/DELETE, return affected rows."""

    async def get_installed_modules(self) -> list[dict]:
        """Fast: SELECT name, state FROM ir_module_module WHERE state='installed'"""

    async def get_db_size(self) -> str:
        """Database size in human-readable format."""

    async def get_table_sizes(self, limit=20) -> list[dict]:
        """Largest tables for diagnostics."""

    async def check_view_integrity(self) -> list[dict]:
        """Find views with invalid arch or broken inheritance."""
```

---

## 7. VERIFICATION LAYER (NEW — Audit Item: Strategic Risk)

The audit correctly identified that AI hallucination on field names is a trust-killer. The verification layer is a mandatory internal component, not an exposed tool.

### 7.1 Live State Cache (`verification/state_cache.py`)

```python
class LiveStateCache:
    """
    In-memory cache of the current Odoo instance state.
    Refreshed after every mutating operation.
    The AI's tool responses include data from this cache
    so the LLM always has current truth in its context.
    """

    def __init__(self, rpc: OdooRPC):
        self.rpc = rpc
        self._installed_modules: set[str] = set()
        self._model_fields: dict[str, dict] = {}  # model → fields_get result
        self._last_refresh: datetime = None

    async def refresh_modules(self) -> set[str]:
        """Re-query installed modules from ir_module_module."""

    async def refresh_model_fields(self, model: str) -> dict:
        """Re-query fields_get for a specific model."""

    async def refresh_all(self) -> None:
        """Full refresh — called after major operations."""

    def is_field_valid(self, model: str, field_name: str) -> bool:
        """Check if a field exists on a model. Uses cache, falls back to live query."""

    def get_model_fields(self, model: str) -> dict | None:
        """Get cached fields for a model, or None if not cached."""
```

### 7.2 Post-Install Verification (`verification/verify_install.py`)

```python
async def verify_module_install(
    rpc: OdooRPC,
    docker: OdooDocker,
    cache: LiveStateCache,
    modules: list[str],
    expected_models: dict[str, list[str]]  # module → expected models
) -> VerificationResult:
    """
    Called automatically after every module install.
    Returns:
        - success: bool
        - installed_modules: list of confirmed installed
        - new_models: list of models now available
        - new_fields_sample: key fields per new model
        - errors: any tracebacks found in logs
        - warnings: any non-critical issues
    """
    # 1. Check Odoo logs for errors
    logs = await docker.logs(service="web", lines=50, grep="ERROR\\|Traceback")

    # 2. Verify module state in ir_module_module
    for module in modules:
        state = rpc.search_read('ir.module.module',
            [['name', '=', module]], ['state'])
        if state[0]['state'] != 'installed':
            ...  # Report failure

    # 3. Verify expected models exist
    for module, models in expected_models.items():
        for model_name in models:
            try:
                rpc.fields_get(model_name)
            except:
                ...  # Model doesn't exist — install failed silently

    # 4. Refresh cache
    await cache.refresh_all()
```

### 7.3 View Integrity Check (`verification/verify_view.py`)

```python
async def verify_view_modification(
    rpc: OdooRPC,
    model: str,
    view_type: str,
    custom_view_id: int
) -> ViewVerificationResult:
    """
    Called after every view modification.
    Tests that the modified view actually renders.
    """
    try:
        # Try to get the compiled view — this will fail if XPath is invalid
        result = rpc.execute(model, 'get_view', [], {
            'view_type': view_type
        })
        return ViewVerificationResult(
            success=True,
            rendered_arch=result['arch'],
            fields_in_view=list(result.get('fields', {}).keys())
        )
    except Exception as e:
        # View is broken — auto-delete the custom view to recover
        rpc.unlink('ir.ui.view', [custom_view_id])
        return ViewVerificationResult(
            success=False,
            error=str(e),
            auto_reverted=True,
            message=f"View modification caused error: {e}. "
                    f"Custom view was automatically reverted."
        )
```

---

## 8. KNOWLEDGE BASE DESIGN

### 8.1 Module Catalog (`knowledge/data/modules.json`)

```json
{
  "sale_management": {
    "display_name": "Sales",
    "technical_name": "sale_management",
    "category": "Sales",
    "summary": "Quotations, sales orders, invoicing",
    "depends": ["sale", "account"],
    "auto_installs": ["sale_stock (if inventory installed)"],
    "key_models": ["sale.order", "sale.order.line", "sale.order.template"],
    "key_settings": {
      "group_sale_pricelist": "Enable pricelists",
      "group_discount_per_so_line": "Allow discounts on order lines",
      "module_sale_margin": "Show margins on orders"
    },
    "common_workflows": [
      "Quotation → Sales Order → Delivery → Invoice",
      "Sales Order → Down Payment → Final Invoice"
    ],
    "configuration_steps": [
      "Install sale_management module",
      "Configure company details and currency",
      "Set up payment terms (account.payment.term)",
      "Create product categories and products",
      "Configure pricelist if needed"
    ],
    "community_limitations": [],
    "oca_alternatives": []
  }
}
```

### 8.2 Community Gaps & OCA Registry (NEW — Audit Item)

```json
// knowledge/data/community_gaps.json
{
  "accounting_reports": {
    "gap": "Odoo 18 Community has no dynamic Balance Sheet, P&L, or General Ledger reports",
    "impact": "critical",
    "affects": ["accounting", "financial_reporting"],
    "enterprise_feature": "Full accounting reports with drill-down",
    "oca_solution": {
      "module": "account_financial_report",
      "repo": "OCA/account-financial-reporting",
      "description": "Full-featured financial reports: Balance Sheet, P&L, Trial Balance, General Ledger, Aged Partner Balance",
      "install_notes": "Requires manual download from OCA GitHub and placement in addons path. Not available via standard Odoo module list.",
      "v18_status": "available"
    },
    "workaround": "Use odoo_db_run_sql to create SQL-based reports, or export data to spreadsheet"
  },
  "payroll": {
    "gap": "No payroll module in Community",
    "impact": "critical_for_hr",
    "oca_solution": {
      "module": "hr_payroll_community",
      "repo": "OCA/payroll",
      "v18_status": "in_progress"
    }
  },
  "document_management": {
    "gap": "No Documents app in Community",
    "impact": "moderate",
    "oca_solution": {
      "module": "dms",
      "repo": "OCA/dms",
      "description": "Document Management System — store and organize files within Odoo"
    }
  },
  "recurring_invoices": {
    "gap": "Limited recurring invoice support in Community",
    "impact": "moderate",
    "oca_solution": {
      "module": "account_invoice_recurring",
      "repo": "OCA/account-invoicing"
    }
  }
}
```

### 8.3 Configuration Recipes

Recipes now include snapshot creation and verification steps:

```json
// knowledge/data/recipes/restaurant.json
{
  "name": "Restaurant Setup",
  "description": "Complete restaurant/food business ERP for Pakistan",
  "version": "1.0",
  "target_audience": "Restaurant owner, no Odoo experience",
  "estimated_time": "5-10 minutes",
  "modules": [
    "point_of_sale", "sale_management", "purchase",
    "stock", "account", "hr", "hr_attendance"
  ],
  "steps": [
    {
      "step": 1,
      "action": "snapshot_create",
      "params": { "name": "pre_restaurant_setup" },
      "description": "Safety snapshot before any changes"
    },
    {
      "step": 2,
      "action": "install_modules",
      "params": { "modules": ["point_of_sale", "purchase", "stock", "account", "hr"] },
      "verify": {
        "models_exist": ["pos.config", "purchase.order", "stock.picking"],
        "check_logs_for_errors": true
      }
    },
    {
      "step": 3,
      "action": "configure_company",
      "params": {
        "customizable_fields": ["name", "street", "city", "country_id", "currency_id", "vat", "phone", "email"],
        "defaults": { "country_id": "Pakistan", "currency_id": "PKR" }
      }
    },
    {
      "step": 4,
      "action": "configure_settings",
      "params": {
        "settings": {
          "pos_module_pos_restaurant": true,
          "pos_iface_splitbill": true,
          "group_stock_multi_locations": true,
          "group_stock_tracking_lot": true
        }
      }
    },
    {
      "step": 5,
      "action": "create_records",
      "model": "product.category",
      "data": [
        {"name": "Food - Ramen", "parent_id": null},
        {"name": "Food - Dumplings", "parent_id": null},
        {"name": "Beverages", "parent_id": null},
        {"name": "Kitchen Supplies", "parent_id": null}
      ],
      "customizable": true
    },
    {
      "step": 6,
      "action": "configure_taxes",
      "description": "Set up Pakistani GST",
      "data": [
        {"name": "GST 17%", "amount": 17.0, "type_tax_use": "sale"},
        {"name": "GST 17% (Purchase)", "amount": 17.0, "type_tax_use": "purchase"}
      ]
    },
    {
      "step": 7,
      "action": "configure_email",
      "description": "Guide user through email setup",
      "interactive": true,
      "required_inputs": ["smtp_host", "smtp_user", "smtp_pass"]
    }
  ],
  "post_setup_checklist": [
    "Add products to POS categories",
    "Configure table layout in Restaurant POS",
    "Create employee accounts and attendance PINs",
    "Set up suppliers for procurement",
    "Configure receipt/invoice template with restaurant branding"
  ]
}
```

---

## 9. DEVELOPMENT PHASES (Revised)

### Phase 1: Foundation + Core CRUD (Week 1-2)
**Goal: Working MCP server talking to a live Odoo instance**

- Project scaffolding with uv + FastMCP
- Docker Compose setup (Odoo 18 + PostgreSQL 17)
- `OdooRPC` client (auth, CRUD, fields_get, search_read)
- `OdooDocker` client (start, stop, restart, logs, exec)
- `OdooPG` client (query, diagnostics)
- First 8 tools: instance_status, instance_logs, instance_start, instance_stop, db_create, db_list, record_search, record_create
- Live State Cache (basic: track installed modules and queried fields)
- Test with Claude Code

**Milestone: "What modules are installed?" + "Create a customer named Steamin" works end-to-end**

### Phase 2: Module Management + Snapshots (Week 2-3)
**Goal: Full module lifecycle with safety net**

- Module install/upgrade/uninstall (dual strategy: CLI + XML-RPC)
- Post-install verification (log check + fields_get + model existence)
- Snapshot create/list/restore/delete (pg_dump via Docker)
- Module introspection tools (model_list, model_fields, model_search_field)
- All remaining CRUD tools (read, update, delete, execute)
- Auto-snapshot before destructive operations

**Milestone: "Install Sales and Inventory, then create a snapshot" works. If install fails, AI detects it.**

### Phase 3: View Customization + Automation (Week 3-4)
**Goal: No-code developer capabilities**

- View list/get_arch/modify/reset tools
- XPath builder utility
- View integrity verification (auto-revert on broken views)
- Automation create/list/update/delete tools
- Email template creation
- Settings get/set tools
- Company configuration tool
- User management tool

**Milestone: "Hide the Tax ID field from the customer form" + "When a sale order over 500,000 PKR is confirmed, email the manager" both work**

### Phase 4: Data Import + Email + Knowledge (Week 4-5)
**Goal: Implementation consultant capabilities**

- Batch import tools (preview, execute, template)
- Email configuration tools (outgoing, incoming, test, DNS guide)
- Knowledge base structure (module catalog, OCA registry, community gaps)
- Populate knowledge for all Community modules + key OCA modules
- Knowledge query tools (module_info, search, community_gaps)
- Diagnostics health check tool

**Milestone: "Import my 500 products from this CSV" + "Set up email for steamin.pk" + "What modules do I need for a restaurant?" all work**

### Phase 5: Recipes + Polish + Distribution (Week 5-6)
**Goal: Ship it**

- Recipe engine (execute multi-step workflows)
- 5 industry recipes (restaurant, ecommerce, manufacturing, services, retail)
- Complete knowledge base content
- Response formatting (markdown + JSON modes)
- Comprehensive error messages (actionable, not technical)
- Documentation and usage guide
- PyPI packaging (`pip install odooforge` / `uvx odooforge`)
- Claude Code + Claude Desktop configuration guides
- Integration tests

**Milestone: "Set up a complete restaurant ERP for Steamin in Lahore" produces a fully configured, working system in under 10 minutes**

### Phase 6: Future — Custom Python Modules (v2)
- Module scaffolding (models, views, security, data files)
- ORM-aware Python code generation
- XML view generation
- Module testing integration
- Git integration
- OCA module auto-download and installation

---

## 10. HOW IT WORKS END-TO-END

### Example: Restaurant Setup (Revised with all audit fixes)

**User**: "I need to set up an ERP for my restaurant Steamin in Lahore. We need POS, inventory tracking, purchases, basic accounting, and employee management. I also want to hide the VAT field from customer forms since we don't use it, and automatically flag any purchase order over 100,000 PKR for my review."

**AI Agent (using OdooForge tools):**

```
1.  odoo_knowledge_search("restaurant POS inventory employees Pakistan")
    → Returns: restaurant recipe, module list, PKR currency setup, GST config

2.  odoo_knowledge_community_gaps(area="accounting")
    → Returns: "No Balance Sheet in Community — suggest OCA account_financial_report"
    → AI informs user about this limitation upfront

3.  odoo_instance_status()
    → Running, Odoo 18, port 8069

4.  odoo_db_create(db_name="steamin", language="en_US", country="PK")
    → Database created, base module initialized

5.  odoo_snapshot_create(db="steamin", name="fresh_install")
    → Safety snapshot before any module installation

6.  odoo_module_install(db="steamin",
        modules=["point_of_sale", "purchase", "stock", "account",
                 "hr", "hr_attendance"])
    → Installs modules via CLI, runs verification:
       ✓ All modules state="installed"
       ✓ Models pos.config, purchase.order, stock.picking exist
       ✓ No errors in logs
       → Cache refreshed with new models/fields

7.  odoo_company_configure(db="steamin",
        name="Steamin", city="Lahore", country="Pakistan",
        currency="PKR", phone="+92-...", email="info@steamin.pk")
    → Company configured

8.  odoo_settings_set(db="steamin", settings={
        "pos_module_pos_restaurant": true,
        "group_stock_multi_locations": true,
        "group_stock_tracking_lot": true
    })
    → POS restaurant mode enabled, multi-location inventory on

9.  odoo_record_create(db="steamin", model="account.tax",
        values=[
            {"name": "GST 17%", "amount": 17.0, "type_tax_use": "sale"},
            {"name": "GST 17% (Purchase)", "amount": 17.0, "type_tax_use": "purchase"}
        ])
    → Pakistani GST configured

10. odoo_view_get_arch(db="steamin", model="res.partner", view_type="form")
    → AI sees the current form layout, finds the "vat" field

11. odoo_view_modify(db="steamin", model="res.partner", view_type="form",
        modifications=[
            {"action": "hide", "target": "vat"}
        ])
    → Creates inherited view, verifies it renders correctly
       ✓ View renders without error
       ✓ "vat" field now invisible

12. odoo_automation_create(db="steamin",
        name="Flag Large Purchase Orders",
        model="purchase.order",
        trigger="on_create_or_write",
        trigger_fields=["amount_total"],
        domain_filter=[["amount_total", ">", 100000]],
        actions=[{
            "type": "update_record",
            "params": {"values": {"priority": "1"}}
        }])
    → Automation created and active

13. odoo_snapshot_create(db="steamin", name="post_initial_setup")
    → Checkpoint after all configuration
```

**Result**: Fully configured restaurant ERP with:
- POS in restaurant mode
- Inventory with lot tracking
- Purchase management with auto-flagging
- Pakistani GST
- Customized customer form (no VAT field)
- Automated purchase order review workflow
- Two snapshots for safety (fresh + post-setup)

---

## 11. INSTALLATION & USAGE

### For Claude Code (recommended for development):
```json
// claude_code_config.json or via claude mcp add
{
  "mcpServers": {
    "odooforge": {
      "command": "uvx",
      "args": ["odooforge"],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_MASTER_PASSWORD": "admin",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "odoo",
        "POSTGRES_PASSWORD": "odoo",
        "DOCKER_COMPOSE_PATH": "/path/to/odooforge/docker"
      }
    }
  }
}
```

### For Claude Desktop:
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "odooforge": {
      "command": "uvx",
      "args": ["odooforge"],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_MASTER_PASSWORD": "admin",
        "DOCKER_COMPOSE_PATH": "/path/to/odooforge/docker"
      }
    }
  }
}
```

### As HTTP server (for remote/multi-client):
```bash
odooforge serve --transport streamable-http --port 8100
```

---

## 12. TOOL COUNT SUMMARY

| Category | Tool Count | Phase |
|---|---|---|
| Instance Management | 5 | Phase 1 |
| Database Management | 6 | Phase 1-2 |
| Snapshot/Rollback | 4 | Phase 2 |
| Module Management | 6 | Phase 2 |
| Model Introspection | 3 | Phase 2 |
| Record CRUD | 6 | Phase 1-2 |
| Batch Import | 3 | Phase 4 |
| View/UI Customization | 5 | Phase 3 |
| Automation | 5 | Phase 3 |
| Email Configuration | 4 | Phase 4 |
| Settings & Users | 4 | Phase 3 |
| Knowledge & Recipes | 6 | Phase 4-5 |
| Diagnostics | 1 | Phase 4 |
| **TOTAL** | **58 tools** | |

---

## 13. KEY RISKS & MITIGATIONS (Updated)

| Risk | Impact | Mitigation |
|---|---|---|
| AI hallucinates field names | Broken create/write operations | **Verification Layer**: validate all fields against live `fields_get()` before write. Live State Cache always current. |
| Bad XPath breaks web UI | 500 error, user locked out | **Auto-revert**: `verify_view` tests render immediately after modification. If broken, deletes custom view automatically. |
| Module install silent failure | AI assumes module works | **Post-install verification**: check logs, verify model existence, confirm module state. |
| Automation rule causes loop | Infinite triggers, data corruption | Validate automation domains, test with dry-run where possible, snapshot before creation. |
| Batch import bad data | Thousands of broken records | **Preview tool** runs first (no commit). Import with `on_error="skip"` by default. |
| Email config wrong credentials | Emails silently fail | **Test email** sent immediately after config. Clear error messages for common issues. |
| Community accounting gap | User asks for Balance Sheet, nothing there | **Knowledge base** proactively warns about CE gaps. Suggests OCA modules. |
| Large result sets overwhelm context | Agent confusion, slow responses | Enforce pagination defaults (limit=20), summarize large results. |
| Docker not running | All tools fail | Health check as first tool call. Clear "Docker not running" error. |
| XML-RPC deprecation (Odoo 20) | Future incompatibility | Connection layer abstracted. JSON-2 adapter planned for v2. |

---

## 14. SUCCESS METRICS (Updated)

- **Zero to configured ERP in < 10 minutes** through conversation (including view customization + automation rules)
- **All 35+ Community modules** installable and configurable via tools
- **View customization success rate > 95%** (auto-revert handles the 5%)
- **Batch import of 1,000+ records** in a single tool call
- **Zero manual Odoo UI interaction required** for initial setup
- **Knowledge base covers 100%** of Community modules + top 20 OCA modules
- **Snapshot/rollback in < 30 seconds** for any database size < 1GB
- **Post-install verification catches 100%** of silent installation failures
- **Email configuration succeeds on first attempt** for major providers (Gmail, Outlook, custom SMTP)
