"""Data model customization patterns for Odoo 18.

Each pattern describes a common customization approach, when to use it,
and the ingredients (OdooForge tools, models, fields) needed to
implement it.
"""

from __future__ import annotations

from typing import Any

PATTERNS: dict[str, dict[str, Any]] = {
    "partner_extension": {
        "name": "Extend Contacts",
        "description": (
            "Add custom fields to the res.partner model to store "
            "industry-specific data on customers, vendors, or contacts "
            "without creating a separate model."
        ),
        "approach": "configuration",
        "when_to_use": (
            "When you need to store additional data on contacts — "
            "e.g., loyalty tier, tax ID type, preferred delivery window, "
            "or industry classification."
        ),
        "ingredients": [
            "Custom x_ fields on res.partner via schema tools",
            "Optional: automated action to set defaults or validate",
            "Optional: add fields to contact form view via view inheritance",
        ],
    },
    "product_extension": {
        "name": "Extend Products",
        "description": (
            "Add custom fields to product.template or product.product "
            "to store additional product metadata — allergens, shelf life, "
            "compliance codes, etc."
        ),
        "approach": "configuration",
        "when_to_use": (
            "When products need extra attributes beyond standard Odoo fields — "
            "e.g., nutritional info for food, hazard class for chemicals, "
            "or warranty period for electronics."
        ),
        "ingredients": [
            "Custom x_ fields on product.template via schema tools",
            "Product attributes for variant-generating properties",
            "Optional: product categories for grouping",
        ],
    },
    "trackable_custom_model": {
        "name": "Custom Model with Tracking",
        "description": (
            "Create a new custom model that inherits mail.thread and "
            "mail.activity.mixin for full chatter support, activity "
            "scheduling, and change tracking."
        ),
        "approach": "code_generation",
        "when_to_use": (
            "When you need a completely new business object with full "
            "audit trail — e.g., a maintenance request, quality check, "
            "or custom approval form."
        ),
        "ingredients": [
            "New ir.model with mail.thread and mail.activity.mixin parents",
            "Standard fields: name, state (Selection), user_id, date, notes",
            "Security: ir.model.access records for relevant groups",
            "Views: form, tree, and optionally kanban",
            "Menu item under an appropriate app",
        ],
    },
    "simple_custom_model": {
        "name": "Simple Custom Model",
        "description": (
            "Create a lightweight custom model for master data or "
            "configuration — no chatter, no workflow, just data storage "
            "with form and list views."
        ),
        "approach": "configuration",
        "when_to_use": (
            "For reference tables, lookup data, or simple configuration "
            "models — e.g., product tags, region codes, service types."
        ),
        "ingredients": [
            "New ir.model via schema tools",
            "Fields: name (Char, required), plus domain-specific fields",
            "Security: ir.model.access for user groups",
            "Views: simple form and tree",
        ],
    },
    "multi_company_model": {
        "name": "Multi-Company Model",
        "description": (
            "Create or extend a model with company_id field and record "
            "rules to ensure data isolation between companies in a "
            "multi-company Odoo setup."
        ),
        "approach": "code_generation",
        "when_to_use": (
            "When the business operates multiple companies/branches and "
            "each company's data must be kept separate."
        ),
        "ingredients": [
            "company_id Many2one field on the model",
            "ir.rule record rule with domain: ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]",
            "Default value: lambda self: self.env.company",
        ],
    },
    "smart_button": {
        "name": "Smart Button on Form",
        "description": (
            "Add a smart button to an existing form view that shows a "
            "count or status and links to related records — e.g., "
            "'3 Invoices' button on a partner form."
        ),
        "approach": "code_generation",
        "when_to_use": (
            "When users need quick navigation between related records — "
            "e.g., showing order count on a customer, or task count on a project."
        ),
        "ingredients": [
            "Computed field for the count/status",
            "Button element in the form view's button_box",
            "Action to open the related records with proper domain filter",
        ],
    },
    "automated_workflow": {
        "name": "Automated Workflow",
        "description": (
            "Use base.automation (automated actions) to create event-driven "
            "workflows — auto-assign, auto-validate, send notifications, "
            "or update fields based on conditions."
        ),
        "approach": "configuration",
        "when_to_use": (
            "When business processes need automation without custom code — "
            "e.g., auto-assign leads by region, send reminder before deadline, "
            "or escalate overdue tasks."
        ),
        "ingredients": [
            "base.automation record with trigger (on_create, on_write, on_time)",
            "Filter domain to target specific records",
            "Action: update fields, send email, create activity, or execute code",
            "Optional: before_update_domain for field-change triggers",
        ],
    },
    "custom_report": {
        "name": "Custom Report",
        "description": (
            "Create a QWeb PDF or HTML report for a model — invoices, "
            "packing slips, certificates, or any document that needs "
            "professional formatting."
        ),
        "approach": "configuration",
        "when_to_use": (
            "When users need printable documents beyond standard Odoo "
            "reports — e.g., custom invoice layout, work order sheet, "
            "or product certificate."
        ),
        "ingredients": [
            "ir.actions.report record linking model to QWeb template",
            "QWeb template with report layout and data fields",
            "Optional: paper format configuration",
            "Optional: report action added to print menu",
        ],
    },
    "kanban_workflow": {
        "name": "Kanban Workflow",
        "description": (
            "Set up a model with a selection or Many2one stage field "
            "and a Kanban view for visual drag-and-drop workflow "
            "management."
        ),
        "approach": "either",
        "when_to_use": (
            "When a process has distinct stages and users benefit from "
            "a visual board — e.g., project tasks, support tickets, "
            "approval requests."
        ),
        "ingredients": [
            "stage_id Many2one field (or selection state field)",
            "Stage model with sequence for ordering",
            "Kanban view with stage grouping (default_group_by)",
            "Optional: automated actions on stage change",
        ],
    },
    "approval_workflow": {
        "name": "Approval Workflow",
        "description": (
            "Add an approval process to a model with states (draft, "
            "submitted, approved, rejected) and group-based permissions "
            "controlling who can approve."
        ),
        "approach": "code_generation",
        "when_to_use": (
            "When records need manager or committee approval before "
            "becoming active — e.g., purchase orders above a threshold, "
            "leave requests, expense reports."
        ),
        "ingredients": [
            "Selection field for state (draft/submitted/approved/rejected)",
            "Button actions for submit, approve, reject, reset to draft",
            "Security groups for approvers",
            "ir.rule to restrict approval actions to approver group",
            "Optional: email notification on state change",
        ],
    },
    "data_import_pipeline": {
        "name": "Data Import Pipeline",
        "description": (
            "Import data from CSV/Excel into Odoo using the built-in "
            "import framework or programmatic record creation with "
            "validation and error handling."
        ),
        "approach": "configuration",
        "when_to_use": (
            "When migrating data from another system or doing bulk "
            "updates — e.g., importing product catalogs, customer lists, "
            "or chart of accounts."
        ),
        "ingredients": [
            "CSV file with column headers matching Odoo field names",
            "External ID (id column) for upsert behavior",
            "Relational fields use external ID or name_search format",
            "Optional: pre-import validation with dry-run",
        ],
    },
    "scheduled_job": {
        "name": "Scheduled Job (Cron)",
        "description": (
            "Create a recurring scheduled action (ir.cron) that runs "
            "at defined intervals to perform maintenance, sync data, "
            "or generate periodic records."
        ),
        "approach": "code_generation",
        "when_to_use": (
            "For periodic tasks — e.g., nightly stock recount, weekly "
            "report generation, daily lead assignment, or external "
            "system synchronization."
        ),
        "ingredients": [
            "ir.cron record with model, method, and interval",
            "Server action or Python code for the logic",
            "interval_type: minutes, hours, days, weeks, months",
            "Optional: nextcall for specific start time",
        ],
    },
    "website_controller": {
        "name": "Website Controller / Page",
        "description": (
            "Create custom website pages or API endpoints using Odoo's "
            "HTTP controller framework for public or portal-facing "
            "functionality."
        ),
        "approach": "code_generation",
        "when_to_use": (
            "When you need custom web pages, REST API endpoints, or "
            "portal features beyond standard Odoo website pages — "
            "e.g., booking forms, status trackers, or webhook receivers."
        ),
        "ingredients": [
            "Controller class inheriting from http.Controller",
            "Route decorators (@http.route) with auth and website flags",
            "QWeb template for HTML rendering",
            "Optional: JSON response for API endpoints",
        ],
    },
}
