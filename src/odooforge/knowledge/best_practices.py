"""Odoo 18 best practices and convention rules.

A structured collection of rules that an AI assistant should follow
when configuring, customizing, or extending an Odoo instance.
"""

from __future__ import annotations

from typing import Any

BEST_PRACTICES: dict[str, Any] = {
    "rules": [
        # ── Naming conventions (3) ────────────────────────────────
        {
            "category": "naming",
            "rule": "Custom fields must use the x_ prefix",
            "why": (
                "Odoo reserves unprefixed field names for core modules. "
                "The x_ prefix marks fields as user-created and prevents "
                "conflicts during module upgrades."
            ),
            "example": "x_loyalty_tier, x_tax_exempt, x_delivery_window",
        },
        {
            "category": "naming",
            "rule": "Custom models must use the x_ prefix",
            "why": (
                "Like fields, custom model technical names must start with "
                "x_ to distinguish them from core models and avoid upgrade "
                "collisions."
            ),
            "example": "x_quality_check, x_booking_slot, x_maintenance_log",
        },
        {
            "category": "naming",
            "rule": "Use snake_case for technical names and Title Case for user-facing labels",
            "why": (
                "Odoo convention uses snake_case for technical names "
                "(field names, model names) and Title Case for string labels "
                "shown in the UI."
            ),
            "example": "Field name: x_delivery_date, Label: 'Delivery Date'",
        },

        # ── Model design (5) ─────────────────────────────────────
        {
            "category": "model_design",
            "rule": "Extend existing models before creating new ones",
            "why": (
                "Adding fields to res.partner, product.template, or "
                "sale.order is simpler and preserves existing workflows. "
                "Only create new models when the data does not logically "
                "belong on an existing model."
            ),
            "example": (
                "Add x_allergens to product.template instead of creating "
                "a separate x_product_allergen model."
            ),
        },
        {
            "category": "model_design",
            "rule": "Add mail.thread inheritance for records that need discussion and tracking",
            "why": (
                "mail.thread provides the chatter (message log), email "
                "integration, and field-change tracking that users expect "
                "on business documents."
            ),
            "example": "Custom model x_maintenance_request should inherit mail.thread.",
        },
        {
            "category": "model_design",
            "rule": "Include a _rec_name or name field on every model",
            "why": (
                "Odoo uses _rec_name (defaults to 'name') for display in "
                "dropdowns, breadcrumbs, and log messages. Without it, "
                "records show as 'x_model,42' which is confusing."
            ),
            "example": "Always add a Char field 'x_name' or set _rec_name to a meaningful field.",
        },
        {
            "category": "model_design",
            "rule": "Use Selection fields for fixed-choice states, Many2one for user-configurable stages",
            "why": (
                "Selection fields are fast and simple for fixed workflows "
                "(draft/confirmed/done). Many2one to a stage model is "
                "better when users need to add/reorder stages."
            ),
            "example": (
                "state = Selection for invoice status; stage_id = Many2one "
                "for CRM pipeline stages."
            ),
        },
        {
            "category": "model_design",
            "rule": "Always define _description on custom models",
            "why": (
                "The _description string appears in the UI (e.g., access "
                "rights configuration, log entries). Without it, users "
                "see the raw technical name."
            ),
            "example": "_description = 'Maintenance Request'",
        },

        # ── Fields (3) ───────────────────────────────────────────
        {
            "category": "fields",
            "rule": "Set required=True only when the field is truly mandatory for business logic",
            "why": (
                "Over-requiring fields frustrates users and blocks imports. "
                "Reserve required=True for fields the system cannot function without."
            ),
            "example": "name is required, but x_notes should not be.",
        },
        {
            "category": "fields",
            "rule": "Use Monetary fields (not Float) for all currency amounts",
            "why": (
                "Monetary fields automatically respect currency precision "
                "and display the correct currency symbol. Float fields "
                "can cause rounding errors in financial calculations."
            ),
            "example": "x_budget_amount = fields.Monetary(currency_field='currency_id')",
        },
        {
            "category": "fields",
            "rule": "Define string labels and help tooltips on every custom field",
            "why": (
                "Clear labels and help text make the UI self-documenting "
                "and reduce support requests. The help text appears as "
                "a tooltip on hover."
            ),
            "example": "x_lead_time = Integer(string='Lead Time (Days)', help='Average days from order to delivery')",
        },

        # ── Security (3) ─────────────────────────────────────────
        {
            "category": "security",
            "rule": "Create access rights (ir.model.access) for every custom model",
            "why": (
                "Models without access rights are invisible to non-admin "
                "users. Every model needs at least one ir.model.access "
                "record per user group."
            ),
            "example": (
                "Grant read/write/create to the user group and "
                "read/write/create/unlink to the manager group."
            ),
        },
        {
            "category": "security",
            "rule": "Use record rules (ir.rule) to restrict data by company in multi-company setups",
            "why": (
                "Without record rules, users in Company A can see and "
                "modify Company B's data. Record rules enforce row-level "
                "data isolation."
            ),
            "example": "domain_force: ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]",
        },
        {
            "category": "security",
            "rule": "Never give admin/superuser access to regular business users",
            "why": (
                "The admin account bypasses all security rules. Regular "
                "users should be assigned to appropriate security groups "
                "with the minimum necessary permissions."
            ),
            "example": "Create dedicated groups like 'Sales / User' and 'Sales / Manager'.",
        },

        # ── Views (3) ────────────────────────────────────────────
        {
            "category": "views",
            "rule": "Always create both form and tree (list) views for custom models",
            "why": (
                "Tree views provide an overview for browsing records; "
                "form views are needed for editing. Without both, the "
                "user experience is incomplete."
            ),
            "example": "Create ir.ui.view records with type='form' and type='tree'.",
        },
        {
            "category": "views",
            "rule": "Use view inheritance (inherit_id) to modify existing views instead of replacing them",
            "why": (
                "Replacing a view loses all other customizations and "
                "may break on upgrade. Inheritance uses XPath to surgically "
                "add or modify specific elements."
            ),
            "example": "inherit_id = 'sale.view_order_form', arch uses xpath to add fields.",
        },
        {
            "category": "views",
            "rule": "Group related fields using <group> and <notebook>/<page> elements",
            "why": (
                "Organized forms are easier to use. Group related fields "
                "together and use tabs (notebook pages) for secondary "
                "information."
            ),
            "example": (
                "Main info in the first group, financial details in a "
                "second group, notes in a separate tab."
            ),
        },

        # ── Automation (2) ───────────────────────────────────────
        {
            "category": "automation",
            "rule": "Prefer server actions and automated rules over custom Python code",
            "why": (
                "Server actions and base.automation rules can be created "
                "and modified through the UI without code deployment. "
                "Use code only when the logic is too complex for declarative rules."
            ),
            "example": (
                "Use an automated action to send an email when stage changes, "
                "instead of overriding the write method."
            ),
        },
        {
            "category": "automation",
            "rule": "Set appropriate triggers and filters on automated actions to avoid performance issues",
            "why": (
                "An automated action without a filter domain runs on every "
                "record write, which can be very slow on large datasets. "
                "Always include a filter to narrow the trigger scope."
            ),
            "example": (
                "Filter: [('stage_id.name', '=', 'Won')] instead of "
                "triggering on every crm.lead write."
            ),
        },

        # ── Reports (1) ──────────────────────────────────────────
        {
            "category": "reports",
            "rule": "Use QWeb templates for PDF reports and inherit existing report templates when possible",
            "why": (
                "QWeb is Odoo's native template engine for reports. "
                "Inheriting existing templates (e.g., account.report_invoice) "
                "preserves the standard layout while allowing targeted modifications."
            ),
            "example": "Inherit 'account.report_invoice_document' to add a custom footer.",
        },

        # ── Performance (2) ──────────────────────────────────────
        {
            "category": "performance",
            "rule": "Add database indexes to fields used frequently in search domains and filters",
            "why": (
                "Fields used in domain filters, group-by operations, or "
                "ORDER BY clauses benefit from indexing. Without indexes, "
                "queries on large tables become slow."
            ),
            "example": "Set index=True on frequently-searched fields like x_region or x_status.",
        },
        {
            "category": "performance",
            "rule": "Use read_group instead of search_read when you only need aggregate data",
            "why": (
                "read_group performs aggregation at the database level "
                "(SQL GROUP BY) which is far more efficient than fetching "
                "all records and aggregating in Python."
            ),
            "example": "rpc.read_group('sale.order', [], ['amount_total:sum'], ['state'])",
        },
    ],
}
