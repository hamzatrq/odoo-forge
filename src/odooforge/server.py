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
