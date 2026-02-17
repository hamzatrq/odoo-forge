"""OdooForge MCP Server — AI-First ERP Configuration Engine.

Entry point for the FastMCP server that exposes all OdooForge tools.
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from odooforge.config import get_config
from odooforge.connections.docker_client import OdooDocker
from odooforge.connections.pg_client import OdooPG
from odooforge.connections.xmlrpc_client import OdooRPC
from odooforge.verification.state_cache import LiveStateCache

logger = logging.getLogger(__name__)


# ── Shared application state ───────────────────────────────────────

@dataclass
class AppState:
    """Shared state for all tools — initialized at server startup."""
    rpc: OdooRPC
    docker: OdooDocker
    pg: OdooPG
    cache: LiveStateCache
    config: Any


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Initialize connections on startup, clean up on shutdown."""
    cfg = get_config()

    rpc = OdooRPC(
        url=cfg.odoo_url,
        db=cfg.odoo_default_db,
        username=cfg.odoo_admin_user,
        password=cfg.odoo_admin_password,
    )

    docker = OdooDocker(compose_path=cfg.docker_compose_path)

    pg = OdooPG(
        host=cfg.postgres_host,
        port=cfg.postgres_port,
        user=cfg.postgres_user,
        password=cfg.postgres_password,
    )

    cache = LiveStateCache(rpc)

    state = AppState(rpc=rpc, docker=docker, pg=pg, cache=cache, config=cfg)

    # Try to authenticate if a default DB is configured
    if cfg.odoo_default_db:
        try:
            rpc.authenticate(cfg.odoo_default_db)
            cache.refresh_modules()
            logger.info("Connected to Odoo database '%s'", cfg.odoo_default_db)
        except Exception as e:
            logger.warning("Could not connect to default database: %s", e)

    try:
        yield state
    finally:
        await pg.close()


# ── MCP Server ─────────────────────────────────────────────────────

mcp = FastMCP(
    "OdooForge",
    instructions=(
        "AI-First ERP Configuration Engine for Odoo 18. "
        "Provides tools for infrastructure management, module installation, "
        "record CRUD, view customization, automation rules, batch import, "
        "and more — all via natural language through MCP."
    ),
    lifespan=app_lifespan,
)


def _state(ctx) -> AppState:
    """Extract AppState from the MCP context."""
    return ctx.request_context.lifespan_context


# ── MCP Resources (Domain Knowledge) ─────────────────────────────

@mcp.resource(
    "odoo://knowledge/modules",
    name="Odoo Module Catalog",
    description="Odoo 18 modules mapped to business needs with descriptions and dependencies.",
    mime_type="application/json",
)
def knowledge_modules() -> str:
    from odooforge.knowledge import get_knowledge_base
    return json.dumps(get_knowledge_base().get_modules(), indent=2)


@mcp.resource(
    "odoo://knowledge/dictionary",
    name="Business-to-Odoo Dictionary",
    description="Maps business terms (customer, invoice, warehouse) to Odoo models with filters and tips.",
    mime_type="application/json",
)
def knowledge_dictionary() -> str:
    from odooforge.knowledge import get_knowledge_base
    return json.dumps(get_knowledge_base().get_dictionary(), indent=2)


@mcp.resource(
    "odoo://knowledge/patterns",
    name="Data Model Patterns",
    description="Common Odoo customization patterns with ingredients and approach (configuration vs code generation).",
    mime_type="application/json",
)
def knowledge_patterns() -> str:
    from odooforge.knowledge import get_knowledge_base
    return json.dumps(get_knowledge_base().get_patterns(), indent=2)


@mcp.resource(
    "odoo://knowledge/best-practices",
    name="Odoo Best Practices",
    description="Odoo conventions and guidelines for naming, security, views, performance, and automation.",
    mime_type="application/json",
)
def knowledge_best_practices() -> str:
    from odooforge.knowledge import get_knowledge_base
    return json.dumps(get_knowledge_base().get_best_practices(), indent=2)


@mcp.resource(
    "odoo://knowledge/blueprints",
    name="Industry Blueprints Index",
    description="List of available industry blueprints with names and descriptions.",
    mime_type="application/json",
)
def knowledge_blueprints_index() -> str:
    from odooforge.knowledge import get_knowledge_base
    kb = get_knowledge_base()
    index = {}
    for bp_id in kb.list_blueprints():
        bp = kb.get_blueprint(bp_id)
        if bp:
            index[bp_id] = {"name": bp["name"], "description": bp["description"]}
    return json.dumps(index, indent=2)


@mcp.resource(
    "odoo://knowledge/blueprints/{industry}",
    name="Industry Blueprint",
    description="Detailed industry blueprint with modules, models, automations, and settings.",
    mime_type="application/json",
)
def knowledge_blueprint(industry: str) -> str:
    from odooforge.knowledge import get_knowledge_base
    kb = get_knowledge_base()
    bp = kb.get_blueprint(industry)
    if bp is None:
        available = kb.list_blueprints()
        return json.dumps({"error": f"Unknown industry: {industry}", "available": available})
    return json.dumps(bp, indent=2)


# ── MCP Prompts (Workflow Templates) ─────────────────────────────


@mcp.prompt(
    name="business-setup",
    description="Set up a complete business on Odoo from a natural language description. "
    "Guides you through requirements analysis, module selection, and configuration.",
)
def prompt_business_setup() -> str:
    return """\
You are an Odoo business setup specialist using OdooForge. Follow this workflow precisely.

## Step 1: Understand the Business

Ask the user to describe their business. Gather:
- Industry and what they sell/do
- Business size (employees, locations)
- How they sell (in-store, online, both)
- Key processes they need (inventory, manufacturing, HR, etc.)
- Any specific requirements or pain points

Ask ONE question at a time. Don't overwhelm.

## Step 2: Analyze Requirements

Read these resources for context:
- odoo://knowledge/modules — to find matching Odoo modules
- odoo://knowledge/blueprints — to check for a matching industry blueprint
- odoo://knowledge/dictionary — to translate business terms to Odoo models

Based on what you learn, identify:
1. Which Odoo modules are needed (and why, in business language)
2. Whether a matching industry blueprint exists
3. What custom fields or models might be needed
4. Any gaps or questions that need clarification

## Step 3: Present the Plan

Present a clear plan to the user in BUSINESS language:
- "I'll set up your point-of-sale system for in-store sales"
- NOT: "I'll install the point_of_sale module"

Structure the plan as phases:
1. Core setup (company, base modules)
2. Industry-specific configuration
3. Custom features
4. Integrations (payments, email, etc.)

Ask the user to approve before proceeding.

## Step 4: Execute

For each phase:
1. Create a snapshot first: odoo_snapshot_create
2. Install needed modules: odoo_module_install
3. Configure settings: odoo_settings_set
4. Add custom fields: odoo_schema_field_create
5. Modify views: odoo_view_modify
6. Create automations: odoo_automation_create
7. Report what was done (in business language)

## Step 5: Verify and Iterate

- Run odoo_diagnostics_health_check
- Summarize everything that was set up
- Ask: "What would you like to adjust or add?"

IMPORTANT: Always create a snapshot before making changes. Always verify after changes.
If something fails, report the error clearly and suggest alternatives.\
"""


@mcp.prompt(
    name="feature-builder",
    description="Add a custom feature to an existing Odoo setup — custom fields, views, automations, or reports.",
)
def prompt_feature_builder() -> str:
    return """\
You are an Odoo feature specialist using OdooForge. Follow this workflow.

## Step 1: Understand the Feature

Ask the user what they want to add. Clarify:
- What business problem does this solve?
- What data needs to be tracked? (fields)
- Where should it appear? (which forms, lists)
- Should anything happen automatically? (automations)
- Who should have access? (security)

## Step 2: Design the Feature

Read these resources:
- odoo://knowledge/dictionary — to find the right Odoo model
- odoo://knowledge/patterns — to match a known customization pattern
- odoo://knowledge/best-practices — for naming and design conventions

Determine the approach:
- **Configuration** (custom fields + view inheritance + automations via existing tools)
- **Code generation** (needs a custom Python module — use odoo_generate_addon when available)

Present the design to the user:
- Which model(s) will be modified
- What fields will be added (name, type, purpose)
- What view changes will be made
- What automations will be created

## Step 3: Implement

1. Create a snapshot: odoo_snapshot_create
2. Create custom fields: odoo_schema_field_create (use x_ prefix)
3. Read current view: odoo_view_get_arch
4. Modify views to show new fields: odoo_view_modify
5. Create automations if needed: odoo_automation_create
6. Create email templates if needed: odoo_email_template_create

## Step 4: Verify

- Check field exists: odoo_model_fields
- Preview the updated view: odoo_view_get_arch
- Test automation triggers if applicable
- Report what was created

## Step 5: Iterate

Ask: "Try it out in Odoo. What would you like to adjust?"

IMPORTANT: Always use x_ prefix for custom fields. Always create a snapshot first.
Read odoo://knowledge/best-practices before making design decisions.\
"""


@mcp.prompt(
    name="module-generator",
    description="Generate a complete custom Odoo addon module with models, views, security, and menus.",
)
def prompt_module_generator() -> str:
    return """\
You are an Odoo module developer using OdooForge. Follow this workflow.

## Step 1: Gather Requirements

Ask the user about their custom module:
- What does the module manage? (what data/process)
- What fields does each record have?
- What views are needed? (list, form, kanban, calendar)
- Who uses it? (user roles and permissions)
- Does it relate to existing Odoo data? (contacts, products, sales orders, etc.)
- Any automations or scheduled jobs?
- Does it need a website controller or API?

## Step 2: Design the Module

Read these resources:
- odoo://knowledge/patterns — for model design patterns
- odoo://knowledge/best-practices — for Odoo conventions
- odoo://knowledge/dictionary — to understand existing models it connects to

Design and present:
- Module name and technical name
- Models with fields, types, and relationships
- View types per model
- Menu structure (where it appears in Odoo)
- Security groups (user vs manager)
- Access rules per group

Follow Odoo conventions from best-practices:
- Models inherit mail.thread for messaging
- Include name, active, company_id fields
- Use ir.sequence for reference numbers
- Create user + manager security groups

## Step 3: Generate

Use odoo_generate_addon (when available) to create the module, OR manually create each component:

For configuration-based features:
1. odoo_schema_model_create — create the model
2. odoo_schema_field_create — add fields (x_ prefix)
3. odoo_view_modify — create/modify views
4. odoo_automation_create — add automations

For full code generation:
1. Generate __manifest__.py
2. Generate models/*.py (Python model classes)
3. Generate views/*.xml (form, tree, kanban views + actions + menus)
4. Generate security/ir.model.access.csv
5. Deploy to addons directory and install

## Step 4: Deploy and Test

Ask the user's preference:
- **Hot reload**: Deploy to mounted addons/ and install immediately
- **Git scaffold**: Create in a directory for version control

After deployment:
- Verify module is installed: odoo_module_list_installed
- Check model exists: odoo_model_list
- Verify fields: odoo_model_fields
- Test creating a record: odoo_record_create

## Step 5: Iterate

Guide the user through testing. Ask what needs adjustment.

IMPORTANT: Always follow Odoo naming conventions. Always create security rules.
Read odoo://knowledge/patterns for the right model design pattern.\
"""


@mcp.prompt(
    name="troubleshooter",
    description="Diagnose and fix issues in an Odoo instance — errors, broken views, module problems, access issues.",
)
def prompt_troubleshooter() -> str:
    return """\
You are an Odoo diagnostic specialist using OdooForge. Follow this workflow.

## Step 1: Assess the Situation

Ask the user what's wrong. Common issues:
- "Something is broken" → need specifics
- "I see an error" → get the error message
- "A page won't load" → which page/model
- "Users can't access X" → access/permissions issue
- "Data looks wrong" → data integrity issue

Run initial diagnostics:
- odoo_diagnostics_health_check — overall system health
- odoo_instance_logs(lines=100, level_filter="ERROR") — recent errors

## Step 2: Identify the Problem

Based on symptoms, investigate:

**Access/Permission errors:**
- odoo_record_search on ir.model.access for the affected model
- odoo_record_search on ir.rule for record-level rules
- Check user's groups: odoo_record_read on res.users

**View/UI errors:**
- odoo_view_list_customizations — check for broken custom views
- odoo_view_get_arch — inspect the problematic view
- Look for malformed XPath or missing field references

**Module errors:**
- odoo_module_list_installed — check module states
- Look for modules in "to upgrade" or "to install" state (stuck)
- odoo_instance_logs with grep for the module name

**Data errors:**
- odoo_record_search on the affected model
- odoo_db_run_sql for direct database inspection
- odoo_model_fields to verify schema matches expectations

## Step 3: Explain

Tell the user what's wrong in PLAIN language:
- "The CRM module didn't finish installing — it's stuck in 'to upgrade' state"
- NOT: "ir.module.module state is 'to upgrade' for crm"

## Step 4: Fix

ALWAYS create a snapshot first: odoo_snapshot_create

Common fixes:
- **Broken view**: odoo_view_reset to restore original
- **Stuck module**: odoo_module_upgrade to retry
- **Missing field**: odoo_schema_field_create or odoo_module_upgrade
- **Access denied**: Create/update ir.model.access via odoo_record_create
- **Data corruption**: odoo_db_run_sql for targeted fixes
- **General issues**: odoo_instance_restart to clear caches

After fixing, verify:
- Re-run odoo_diagnostics_health_check
- Check the specific issue is resolved

## Step 5: Prevent

Explain what caused the issue and how to avoid it:
- "This happened because the module was uninstalled while dependent modules existed"
- "To prevent this, always check dependencies before uninstalling"

IMPORTANT: Always snapshot before fixing. Never run destructive SQL without user confirmation.
If unsure, check odoo_instance_logs for more context before acting.\
"""


# ── Instance Management Tools ──────────────────────────────────────

@mcp.tool()
async def odoo_instance_start(ctx: Context, port: int = 8069) -> dict:
    """Start the Odoo Docker environment (Odoo + PostgreSQL).
    Brings up both containers and waits for Odoo to be healthy.
    """
    from odooforge.tools.instance import odoo_instance_start as _impl
    s = _state(ctx)
    return await _impl(s.docker, s.rpc, port=port)


@mcp.tool()
async def odoo_instance_stop(ctx: Context, remove_volumes: bool = False) -> dict:
    """Stop the running Odoo Docker environment.
    Set remove_volumes=true to also erase all data (DESTRUCTIVE).
    """
    from odooforge.tools.instance import odoo_instance_stop as _impl
    s = _state(ctx)
    return await _impl(s.docker, remove_volumes=remove_volumes)


@mcp.tool()
async def odoo_instance_restart(ctx: Context) -> dict:
    """Restart the Odoo service (not PostgreSQL).
    Useful after configuration changes or to reload the registry.
    """
    from odooforge.tools.instance import odoo_instance_restart as _impl
    s = _state(ctx)
    return await _impl(s.docker)


@mcp.tool()
async def odoo_instance_status(ctx: Context) -> dict:
    """Returns health status of all containers, ports, and Odoo version."""
    from odooforge.tools.instance import odoo_instance_status as _impl
    s = _state(ctx)
    return await _impl(s.docker, s.rpc)


@mcp.tool()
async def odoo_instance_logs(
    ctx: Context,
    lines: int = 100,
    level_filter: str | None = None,
    since: str | None = None,
    grep: str | None = None,
) -> dict:
    """Retrieve Odoo server logs. Filter by level, time range, or regex pattern."""
    from odooforge.tools.instance import odoo_instance_logs as _impl
    s = _state(ctx)
    return await _impl(s.docker, lines=lines, level_filter=level_filter, since=since, grep=grep)


# ── Database Management Tools ─────────────────────────────────────

@mcp.tool()
async def odoo_db_create(
    ctx: Context,
    db_name: str,
    language: str = "en_US",
    country: str | None = None,
    demo_data: bool = False,
    admin_password: str = "admin",
) -> dict:
    """Create a new Odoo database and initialize the base module.
    After creation, the tool authenticates as admin on the new database.
    """
    from odooforge.tools.database import odoo_db_create as _impl
    s = _state(ctx)
    return await _impl(
        s.rpc, s.cache, s.config.odoo_master_password,
        db_name, language=language, country=country,
        demo_data=demo_data, admin_password=admin_password,
    )


@mcp.tool()
async def odoo_db_list(ctx: Context) -> dict:
    """List all databases on the Odoo instance."""
    from odooforge.tools.database import odoo_db_list as _impl
    s = _state(ctx)
    return await _impl(s.rpc)


@mcp.tool()
async def odoo_db_backup(ctx: Context, db_name: str) -> dict:
    """Create a backup of a database using pg_dump."""
    from odooforge.tools.database import odoo_db_backup as _impl
    s = _state(ctx)
    return await _impl(s.docker, db_name)


@mcp.tool()
async def odoo_db_restore(
    ctx: Context, db_name: str, backup_name: str, overwrite: bool = False,
) -> dict:
    """Restore a database from a backup snapshot.
    Set overwrite=true to replace an existing database.
    """
    from odooforge.tools.database import odoo_db_restore as _impl
    s = _state(ctx)
    return await _impl(s.docker, s.rpc, s.cache, db_name, backup_name, overwrite=overwrite)


@mcp.tool()
async def odoo_db_drop(ctx: Context, db_name: str, confirm: bool = False) -> dict:
    """Drop a database permanently. Set confirm=true to proceed."""
    from odooforge.tools.database import odoo_db_drop as _impl
    s = _state(ctx)
    return await _impl(s.rpc, s.config.odoo_master_password, db_name, confirm=confirm)


@mcp.tool()
async def odoo_db_run_sql(
    ctx: Context, db_name: str, query: str, params: list | None = None,
) -> dict:
    """Execute a raw SQL query against a database.
    Returns rows for SELECT queries, execution status for others.
    ⚠️ Bypasses Odoo's ORM — use with caution.
    """
    from odooforge.tools.database import odoo_db_run_sql as _impl
    s = _state(ctx)
    return await _impl(s.pg, db_name, query, params=params)


# ── Record CRUD Tools ──────────────────────────────────────────────

@mcp.tool()
async def odoo_record_search(
    ctx: Context,
    db_name: str,
    model: str,
    domain: list | None = None,
    fields: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
    order: str | None = None,
) -> dict:
    """Search for records in any Odoo model.
    Use domain filters like [["is_company", "=", true]].
    Returns paginated results with total count.
    """
    from odooforge.tools.records import odoo_record_search as _impl
    s = _state(ctx)
    return await _impl(
        s.rpc, db_name, model, domain=domain, fields=fields,
        limit=limit, offset=offset, order=order,
    )


@mcp.tool()
async def odoo_record_read(
    ctx: Context, db_name: str, model: str, ids: list[int], fields: list[str] | None = None,
) -> dict:
    """Read specific records by ID from any model."""
    from odooforge.tools.records import odoo_record_read as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, model, ids, fields=fields)


@mcp.tool()
async def odoo_record_create(
    ctx: Context, db_name: str, model: str, values: dict | list[dict],
) -> dict:
    """Create one or more records in any Odoo model.
    Field names are validated against the live schema before writing.
    """
    from odooforge.tools.records import odoo_record_create as _impl
    s = _state(ctx)
    return await _impl(s.rpc, s.cache, db_name, model, values)


@mcp.tool()
async def odoo_record_update(
    ctx: Context, db_name: str, model: str, ids: list[int], values: dict,
) -> dict:
    """Update existing records. Field names are validated before writing."""
    from odooforge.tools.records import odoo_record_update as _impl
    s = _state(ctx)
    return await _impl(s.rpc, s.cache, db_name, model, ids, values)


@mcp.tool()
async def odoo_record_delete(
    ctx: Context, db_name: str, model: str, ids: list[int], confirm: bool = False,
) -> dict:
    """Delete records. Set confirm=true to proceed (cannot be undone)."""
    from odooforge.tools.records import odoo_record_delete as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, model, ids, confirm=confirm)


@mcp.tool()
async def odoo_record_execute(
    ctx: Context,
    db_name: str,
    model: str,
    method: str,
    args: list | None = None,
    kwargs: dict | None = None,
) -> dict:
    """Execute any method on any model (generic escape hatch).
    Use this for methods not covered by other tools.
    """
    from odooforge.tools.records import odoo_record_execute as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, model, method, args=args, kwargs=kwargs)


# ── Snapshot Tools ─────────────────────────────────────────────────

@mcp.tool()
async def odoo_snapshot_create(
    ctx: Context, db_name: str, name: str, description: str = "",
) -> dict:
    """Create a named snapshot (backup) of a database.
    Use before risky operations like module installs or view modifications.
    """
    from odooforge.tools.snapshots import odoo_snapshot_create as _impl
    s = _state(ctx)
    return await _impl(s.docker, db_name, name, description=description)


@mcp.tool()
async def odoo_snapshot_list(ctx: Context, db_name: str | None = None) -> dict:
    """List all available snapshots, optionally filtered by database."""
    from odooforge.tools.snapshots import odoo_snapshot_list as _impl
    s = _state(ctx)
    return await _impl(s.docker, db_name=db_name)


@mcp.tool()
async def odoo_snapshot_restore(ctx: Context, db_name: str, snapshot_name: str) -> dict:
    """Restore a database from a previously created snapshot.
    ⚠️ This replaces the current database contents entirely.
    """
    from odooforge.tools.snapshots import odoo_snapshot_restore as _impl
    s = _state(ctx)
    return await _impl(s.docker, s.rpc, s.cache, db_name, snapshot_name)


@mcp.tool()
async def odoo_snapshot_delete(ctx: Context, name: str) -> dict:
    """Delete a snapshot from disk to free space."""
    from odooforge.tools.snapshots import odoo_snapshot_delete as _impl
    s = _state(ctx)
    return await _impl(s.docker, name)


# ── Module Management Tools ───────────────────────────────────────

@mcp.tool()
async def odoo_module_list_available(
    ctx: Context, db_name: str, category: str | None = None,
) -> dict:
    """List all modules available for installation, optionally filtered by category."""
    from odooforge.tools.modules import odoo_module_list_available as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, category=category)


@mcp.tool()
async def odoo_module_list_installed(ctx: Context, db_name: str) -> dict:
    """List all currently installed modules."""
    from odooforge.tools.modules import odoo_module_list_installed as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name)


@mcp.tool()
async def odoo_module_info(ctx: Context, db_name: str, module_name: str) -> dict:
    """Get detailed information about a specific module including dependencies."""
    from odooforge.tools.modules import odoo_module_info as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, module_name)


@mcp.tool()
async def odoo_module_install(ctx: Context, db_name: str, modules: list[str]) -> dict:
    """Install one or more Odoo modules with automatic dependency resolution.
    Post-install verification checks module state and error logs.
    """
    from odooforge.tools.modules import odoo_module_install as _impl
    s = _state(ctx)
    return await _impl(s.rpc, s.docker, s.cache, db_name, modules)


@mcp.tool()
async def odoo_module_upgrade(ctx: Context, db_name: str, modules: list[str]) -> dict:
    """Upgrade (update) installed modules to apply changes."""
    from odooforge.tools.modules import odoo_module_upgrade as _impl
    s = _state(ctx)
    return await _impl(s.rpc, s.docker, s.cache, db_name, modules)


@mcp.tool()
async def odoo_module_uninstall(
    ctx: Context, db_name: str, module_name: str, confirm: bool = False,
) -> dict:
    """Uninstall a module. Set confirm=true to proceed.
    ⚠️ May delete data created by the module. Create a snapshot first!
    """
    from odooforge.tools.modules import odoo_module_uninstall as _impl
    s = _state(ctx)
    return await _impl(s.rpc, s.docker, s.cache, db_name, module_name, confirm=confirm)


# ── Model Introspection Tools ─────────────────────────────────────

@mcp.tool()
async def odoo_model_list(
    ctx: Context, db_name: str, search: str | None = None, transient: bool = False,
) -> dict:
    """List all available models (database tables) in Odoo.
    Filter by name/description with search. Set transient=true to include wizard models.
    """
    from odooforge.tools.models import odoo_model_list as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, search=search, transient=transient)


@mcp.tool()
async def odoo_model_fields(
    ctx: Context, db_name: str, model: str,
    field_type: str | None = None, search: str | None = None,
) -> dict:
    """Get all fields of a model with types and attributes.
    This is the source of truth for what fields exist. Filter by type or search.
    """
    from odooforge.tools.models import odoo_model_fields as _impl
    s = _state(ctx)
    return await _impl(s.rpc, s.cache, db_name, model, field_type=field_type, search=search)


@mcp.tool()
async def odoo_model_search_field(
    ctx: Context, db_name: str, query: str, model: str | None = None,
) -> dict:
    """Search for fields across all models or within a specific model.
    Useful when you know a field exists but aren't sure which model it's on.
    """
    from odooforge.tools.models import odoo_model_search_field as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, query, model=model)


# ── Schema Extension Tools ────────────────────────────────────────

@mcp.tool()
async def odoo_schema_field_create(
    ctx: Context, db_name: str, model: str, field_name: str,
    field_type: str, field_label: str,
    required: bool = False,
    selection_options: list[list[str]] | None = None,
    relation_model: str | None = None,
    help_text: str | None = None,
    default_value: str | None = None,
    copied: bool = True,
) -> dict:
    """Create a new custom field on an existing model.
    Field name MUST start with 'x_'. No Python code needed.
    """
    from odooforge.tools.schema import odoo_schema_field_create as _impl
    s = _state(ctx)
    return await _impl(
        s.rpc, s.docker, s.cache, db_name, model, field_name,
        field_type, field_label, required=required,
        selection_options=selection_options, relation_model=relation_model,
        help_text=help_text, default_value=default_value, copied=copied,
    )


@mcp.tool()
async def odoo_schema_field_update(
    ctx: Context, db_name: str, model: str, field_name: str, updates: dict,
) -> dict:
    """Update properties of an existing custom field (x_ prefix only)."""
    from odooforge.tools.schema import odoo_schema_field_update as _impl
    s = _state(ctx)
    return await _impl(s.rpc, s.cache, db_name, model, field_name, updates)


@mcp.tool()
async def odoo_schema_field_delete(
    ctx: Context, db_name: str, model: str, field_name: str, confirm: bool = False,
) -> dict:
    """Delete a custom field from a model. Set confirm=true to proceed.
    ⚠️ This permanently removes the field and all its data.
    """
    from odooforge.tools.schema import odoo_schema_field_delete as _impl
    s = _state(ctx)
    return await _impl(s.rpc, s.docker, s.cache, db_name, model, field_name, confirm=confirm)


@mcp.tool()
async def odoo_schema_model_create(
    ctx: Context, db_name: str, model_name: str, model_label: str,
    fields: list[dict] | None = None,
) -> dict:
    """Create a new custom model (database table).
    Model name MUST start with 'x_'. Optionally create fields at the same time.
    """
    from odooforge.tools.schema import odoo_schema_model_create as _impl
    s = _state(ctx)
    return await _impl(s.rpc, s.docker, s.cache, db_name, model_name, model_label, fields=fields)


@mcp.tool()
async def odoo_schema_list_custom(ctx: Context, db_name: str) -> dict:
    """List all custom (manually created) fields and models."""
    from odooforge.tools.schema import odoo_schema_list_custom as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name)


# ── View Management Tools ─────────────────────────────────────────

@mcp.tool()
async def odoo_view_list(
    ctx: Context, db_name: str, model: str | None = None, view_type: str | None = None,
) -> dict:
    """List views, optionally filtered by model or type (form, tree, kanban, search)."""
    from odooforge.tools.views import odoo_view_list as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, model=model, view_type=view_type)


@mcp.tool()
async def odoo_view_get_arch(
    ctx: Context, db_name: str, view_id: int | None = None,
    model: str | None = None, view_type: str = "form",
) -> dict:
    """Get the full architecture XML of a view. Specify view_id or model+view_type."""
    from odooforge.tools.views import odoo_view_get_arch as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, view_id=view_id, model=model, view_type=view_type)


@mcp.tool()
async def odoo_view_modify(
    ctx: Context, db_name: str, inherit_view_id: int,
    view_name: str, xpath_specs: list[dict],
) -> dict:
    """Modify a view using XPath inheritance. Creates an inheriting view.
    xpath_specs: [{"expr": "//field[@name='email']", "position": "after", "content": "<field name='x_custom'/>"}]
    """
    from odooforge.tools.views import odoo_view_modify as _impl
    s = _state(ctx)
    return await _impl(s.rpc, s.docker, db_name, inherit_view_id, view_name, xpath_specs)


@mcp.tool()
async def odoo_view_reset(
    ctx: Context, db_name: str, view_id: int, confirm: bool = False,
) -> dict:
    """Delete a custom inheriting view to revert the parent view. Set confirm=true."""
    from odooforge.tools.views import odoo_view_reset as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, view_id, confirm=confirm)


@mcp.tool()
async def odoo_view_list_customizations(
    ctx: Context, db_name: str, model: str | None = None,
) -> dict:
    """List all custom (inheriting) views that can be reset."""
    from odooforge.tools.views import odoo_view_list_customizations as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, model=model)


# ── QWeb Report Tools ─────────────────────────────────────────────

@mcp.tool()
async def odoo_report_list(
    ctx: Context, db_name: str, model: str | None = None,
) -> dict:
    """List all available reports, optionally filtered by model."""
    from odooforge.tools.reports import odoo_report_list as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, model=model)


@mcp.tool()
async def odoo_report_get_template(
    ctx: Context, db_name: str, report_name: str,
) -> dict:
    """Get the QWeb template XML of a report by technical name."""
    from odooforge.tools.reports import odoo_report_get_template as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, report_name)


@mcp.tool()
async def odoo_report_modify(
    ctx: Context, db_name: str, template_id: int,
    xpath_specs: list[dict], view_name: str | None = None,
) -> dict:
    """Modify a QWeb report template using XPath inheritance."""
    from odooforge.tools.reports import odoo_report_modify as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, template_id, xpath_specs, view_name=view_name)


@mcp.tool()
async def odoo_report_preview(
    ctx: Context, db_name: str, report_name: str, record_ids: list[int],
) -> dict:
    """Generate a report preview for specific records."""
    from odooforge.tools.reports import odoo_report_preview as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, report_name, record_ids)


@mcp.tool()
async def odoo_report_reset(
    ctx: Context, db_name: str, view_id: int, confirm: bool = False,
) -> dict:
    """Remove a custom report template modification. Set confirm=true."""
    from odooforge.tools.reports import odoo_report_reset as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, view_id, confirm=confirm)


@mcp.tool()
async def odoo_report_layout_configure(
    ctx: Context, db_name: str, paperformat: str | None = None,
    logo: str | None = None, company_name: str | None = None,
) -> dict:
    """Configure report layout (paper format, company logo/name)."""
    from odooforge.tools.reports import odoo_report_layout_configure as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, paperformat=paperformat, logo=logo, company_name=company_name)


# ── Automation Tools ──────────────────────────────────────────────

@mcp.tool()
async def odoo_automation_list(
    ctx: Context, db_name: str, model: str | None = None, trigger: str | None = None,
) -> dict:
    """List all automated actions, optionally filtered by model or trigger type."""
    from odooforge.tools.automation import odoo_automation_list as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, model=model, trigger=trigger)


@mcp.tool()
async def odoo_automation_create(
    ctx: Context, db_name: str, name: str, model: str, trigger: str,
    action_type: str = "code", code: str | None = None,
    filter_domain: str | None = None,
    trigger_fields: list[str] | None = None,
) -> dict:
    """Create a new automated action rule with a server action."""
    from odooforge.tools.automation import odoo_automation_create as _impl
    s = _state(ctx)
    return await _impl(
        s.rpc, db_name, name, model, trigger,
        action_type=action_type, code=code,
        filter_domain=filter_domain, trigger_fields=trigger_fields,
    )


@mcp.tool()
async def odoo_automation_update(
    ctx: Context, db_name: str, rule_id: int, updates: dict,
) -> dict:
    """Update an existing automation rule."""
    from odooforge.tools.automation import odoo_automation_update as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, rule_id, updates)


@mcp.tool()
async def odoo_automation_delete(
    ctx: Context, db_name: str, rule_id: int, confirm: bool = False,
) -> dict:
    """Delete an automation rule. Set confirm=true to proceed."""
    from odooforge.tools.automation import odoo_automation_delete as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, rule_id, confirm=confirm)


@mcp.tool()
async def odoo_email_template_create(
    ctx: Context, db_name: str, name: str, model: str,
    subject: str, body_html: str,
    email_from: str | None = None, reply_to: str | None = None,
) -> dict:
    """Create an email template for automations or manual sends."""
    from odooforge.tools.automation import odoo_email_template_create as _impl
    s = _state(ctx)
    return await _impl(
        s.rpc, db_name, name, model, subject, body_html,
        email_from=email_from, reply_to=reply_to,
    )


# ── Network Tools ─────────────────────────────────────────────────

@mcp.tool()
async def odoo_network_expose(
    ctx: Context, port: int = 8069, method: str = "ssh",
    subdomain: str | None = None,
) -> dict:
    """Expose local Odoo to the internet via tunnel (SSH or Cloudflare)."""
    from odooforge.tools.network import odoo_network_expose as _impl
    return await _impl(port=port, method=method, subdomain=subdomain)


@mcp.tool()
async def odoo_network_status(ctx: Context) -> dict:
    """Check active network tunnels."""
    from odooforge.tools.network import odoo_network_status as _impl
    return await _impl()


@mcp.tool()
async def odoo_network_stop(ctx: Context, port: int | None = None) -> dict:
    """Stop network tunnels. Omit port to stop all."""
    from odooforge.tools.network import odoo_network_stop as _impl
    return await _impl(port=port)


# ── Import Tools ──────────────────────────────────────────────────

@mcp.tool()
async def odoo_import_preview(
    ctx: Context, db_name: str, model: str, csv_data: str,
    has_header: bool = True,
) -> dict:
    """Preview a CSV import — validates fields and shows what would be imported."""
    from odooforge.tools.imports import odoo_import_preview as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, model, csv_data, has_header=has_header)


@mcp.tool()
async def odoo_import_execute(
    ctx: Context, db_name: str, model: str, csv_data: str,
    has_header: bool = True, on_error: str = "stop",
) -> dict:
    """Execute a CSV import into a model. Use odoo_import_preview first."""
    from odooforge.tools.imports import odoo_import_execute as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, model, csv_data, has_header=has_header, on_error=on_error)


@mcp.tool()
async def odoo_import_template(
    ctx: Context, db_name: str, model: str,
    include_optional: bool = False,
) -> dict:
    """Generate a CSV template with correct headers for importing into a model."""
    from odooforge.tools.imports import odoo_import_template as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, model, include_optional=include_optional)


# ── Email Configuration Tools ─────────────────────────────────────

@mcp.tool()
async def odoo_email_configure_outgoing(
    ctx: Context, db_name: str, name: str, smtp_host: str,
    smtp_port: int = 587, smtp_user: str | None = None,
    smtp_pass: str | None = None, smtp_encryption: str = "starttls",
    email_from: str | None = None,
) -> dict:
    """Configure an outgoing SMTP mail server."""
    from odooforge.tools.email import odoo_email_configure_outgoing as _impl
    s = _state(ctx)
    return await _impl(
        s.rpc, db_name, name, smtp_host,
        smtp_port=smtp_port, smtp_user=smtp_user, smtp_pass=smtp_pass,
        smtp_encryption=smtp_encryption, email_from=email_from,
    )


@mcp.tool()
async def odoo_email_configure_incoming(
    ctx: Context, db_name: str, name: str,
    server_type: str = "imap", host: str = "",
    port: int = 993, user: str = "", password: str = "",
    ssl: bool = True,
) -> dict:
    """Configure an incoming IMAP/POP3 mail server."""
    from odooforge.tools.email import odoo_email_configure_incoming as _impl
    s = _state(ctx)
    return await _impl(
        s.rpc, db_name, name, server_type=server_type,
        host=host, port=port, user=user, password=password, ssl=ssl,
    )


@mcp.tool()
async def odoo_email_test(
    ctx: Context, db_name: str, to_address: str,
    subject: str = "OdooForge Test Email",
    body: str = "This is a test email from OdooForge.",
) -> dict:
    """Send a test email to verify SMTP configuration."""
    from odooforge.tools.email import odoo_email_test as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, to_address, subject=subject, body=body)


@mcp.tool()
async def odoo_email_dns_guide(ctx: Context, domain: str) -> dict:
    """Generate DNS records guide (SPF, DKIM, DMARC) for email deliverability."""
    from odooforge.tools.email import odoo_email_dns_guide as _impl
    return await _impl(domain)


# ── Settings & Company Tools ──────────────────────────────────────

@mcp.tool()
async def odoo_settings_get(
    ctx: Context, db_name: str, keys: list[str] | None = None,
) -> dict:
    """Get system settings. Optionally specify keys to retrieve specific values."""
    from odooforge.tools.settings import odoo_settings_get as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, keys=keys)


@mcp.tool()
async def odoo_settings_set(ctx: Context, db_name: str, values: dict) -> dict:
    """Update system settings and apply them."""
    from odooforge.tools.settings import odoo_settings_set as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, values)


@mcp.tool()
async def odoo_company_configure(ctx: Context, db_name: str, updates: dict) -> dict:
    """Configure main company details (name, address, logo, currency, etc.)."""
    from odooforge.tools.settings import odoo_company_configure as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, updates)


@mcp.tool()
async def odoo_users_manage(
    ctx: Context, db_name: str, action: str = "list",
    user_id: int | None = None, values: dict | None = None,
) -> dict:
    """Manage users — list, create, update, activate, deactivate."""
    from odooforge.tools.settings import odoo_users_manage as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, action=action, user_id=user_id, values=values)


# ── Knowledge Tools ───────────────────────────────────────────────

@mcp.tool()
async def odoo_knowledge_module_info(ctx: Context, module_name: str) -> dict:
    """Get curated knowledge about a module — models, fields, workflows, customizations."""
    from odooforge.tools.knowledge import odoo_knowledge_module_info as _impl
    return await _impl(module_name)


@mcp.tool()
async def odoo_knowledge_search(ctx: Context, query: str) -> dict:
    """Search the knowledge base for Odoo information."""
    from odooforge.tools.knowledge import odoo_knowledge_search as _impl
    return await _impl(query)


@mcp.tool()
async def odoo_knowledge_community_gaps(ctx: Context, db_name: str) -> dict:
    """Analyze installed modules and suggest missing modules/configurations."""
    from odooforge.tools.knowledge import odoo_knowledge_community_gaps as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name)


# ── Diagnostics ───────────────────────────────────────────────────

@mcp.tool()
async def odoo_diagnostics_health_check(ctx: Context, db_name: str) -> dict:
    """Run a comprehensive health check: Docker, DB, auth, modules, logs."""
    from odooforge.tools.diagnostics import odoo_diagnostics_health_check as _impl
    s = _state(ctx)
    return await _impl(s.rpc, s.docker, s.pg, db_name)


# ── Planning Tools ────────────────────────────────────────────────

@mcp.tool()
async def odoo_analyze_requirements(ctx: Context, description: str) -> dict:
    """Analyze a business description and return structured Odoo requirements.
    Identifies matching blueprints, needed modules, custom requirements, and questions.
    Example: 'I run a bakery with 3 locations and delivery'
    """
    from odooforge.tools.planning import odoo_analyze_requirements as _impl
    return await _impl(description)


@mcp.tool()
async def odoo_design_solution(
    ctx: Context,
    requirements: dict,
    user_answers: dict | None = None,
) -> dict:
    """Turn analyzed requirements into a phased execution plan (DAG).
    Takes output from odoo_analyze_requirements + optional user answers.
    Returns phases with tool calls, dependencies, and parallelization hints.
    """
    from odooforge.tools.planning import odoo_design_solution as _impl
    return await _impl(requirements, user_answers)


@mcp.tool()
async def odoo_validate_plan(ctx: Context, plan: dict) -> dict:
    """Validate an execution plan before running it.
    Checks module compatibility, field naming, dependency ordering, and safety.
    Returns pass/warning/fail for each check with recommendations.
    """
    from odooforge.tools.planning import odoo_validate_plan as _impl
    return await _impl(plan)


# ── Workflow Tools ────────────────────────────────────────────────

@mcp.tool()
async def odoo_setup_business(
    ctx: Context,
    blueprint_name: str,
    company_name: str,
    db_name: str,
    locations: int = 1,
    dry_run: bool = True,
) -> dict:
    """Set up a complete business from an industry blueprint.
    Returns a step-by-step execution plan. Use dry_run=False to get steps ready for execution.
    Available blueprints: bakery, restaurant, ecommerce, manufacturing, services, retail, healthcare, education, real_estate.
    """
    from odooforge.tools.workflows import odoo_setup_business as _impl
    return await _impl(blueprint_name, company_name, db_name, locations, dry_run)


@mcp.tool()
async def odoo_create_feature(
    ctx: Context,
    feature_name: str,
    target_model: str,
    fields: list[dict],
    db_name: str,
    add_to_views: bool = True,
    automation: dict | None = None,
    dry_run: bool = True,
) -> dict:
    """Build a complete feature on a model in one call.
    Generates steps to create fields, modify views, and optionally add automation.
    Each field dict needs: name, type, label.
    """
    from odooforge.tools.workflows import odoo_create_feature as _impl
    return await _impl(feature_name, target_model, fields, db_name, add_to_views, automation, dry_run)


@mcp.tool()
async def odoo_create_dashboard(
    ctx: Context,
    dashboard_name: str,
    metrics: list[dict],
    db_name: str,
    dry_run: bool = True,
) -> dict:
    """Build a management dashboard with graph/pivot views and menu items.
    Each metric dict needs: model, measure, label.
    Returns a step-by-step execution plan.
    """
    from odooforge.tools.workflows import odoo_create_dashboard as _impl
    return await _impl(dashboard_name, metrics, db_name, dry_run)


@mcp.tool()
async def odoo_setup_integration(
    ctx: Context,
    integration_type: str,
    provider: str,
    db_name: str,
    settings: dict,
    dry_run: bool = True,
) -> dict:
    """Configure an external integration (email, payment, or shipping).
    Generates steps to install modules, configure providers, and test connections.
    Supported types: email, payment, shipping.
    """
    from odooforge.tools.workflows import odoo_setup_integration as _impl
    return await _impl(integration_type, provider, db_name, settings, dry_run)


# ── Code Generation ──────────────────────────────────────────────

@mcp.tool()
async def odoo_generate_addon(
    ctx: Context,
    module_name: str,
    models: list[dict],
    version: str = "18.0.1.0.0",
    author: str = "OdooForge",
    category: str = "Customizations",
    description: str = "",
    depends: list[str] | None = None,
    security_groups: list[dict] | None = None,
) -> dict:
    """Generate a complete installable Odoo 18 module as code.
    Returns all file contents (manifest, models, views, security).
    Each model dict needs: name, description, fields (list of {name, type, string}).
    Optional: inherit (list of mixins like 'mail.thread'), security_groups.
    """
    from odooforge.tools.codegen import odoo_generate_addon as _impl
    return await _impl(module_name, models, version, author, category, description, depends, security_groups)


# ── Recipe Tools ──────────────────────────────────────────────────

@mcp.tool()
async def odoo_recipe_list(ctx: Context) -> dict:
    """List all available industry setup recipes (restaurant, ecommerce, etc.)."""
    from odooforge.tools.recipes import odoo_recipe_list as _impl
    return await _impl()


@mcp.tool()
async def odoo_recipe_execute(
    ctx: Context, db_name: str, recipe_id: str, dry_run: bool = True,
) -> dict:
    """Execute an industry recipe. Use dry_run=True to preview first."""
    from odooforge.tools.recipes import odoo_recipe_execute as _impl
    s = _state(ctx)
    return await _impl(s.rpc, db_name, recipe_id, dry_run=dry_run)


# ── Entry point ────────────────────────────────────────────────────

def main():
    """CLI entry point for running the OdooForge MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    mcp.run()


if __name__ == "__main__":
    main()
