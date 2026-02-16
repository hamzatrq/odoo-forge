"""Business-term-to-Odoo-model dictionary.

Maps everyday business language to the correct Odoo models, filters,
and usage tips so an AI assistant can translate user intent into the
right technical calls.
"""

from __future__ import annotations

from typing import Any

DICTIONARY: dict[str, dict[str, Any]] = {
    # ── People & Contacts ─────────────────────────────────────────
    "customer": {
        "model": "res.partner",
        "filter": [["customer_rank", ">", 0]],
        "description": (
            "Customers are stored in the unified contacts model (res.partner). "
            "The customer_rank field distinguishes customers from other contacts."
        ),
        "tips": (
            "Use is_company=True for company customers, False for individuals. "
            "A contact can be both customer and vendor simultaneously."
        ),
    },
    "vendor": {
        "model": "res.partner",
        "filter": [["supplier_rank", ">", 0]],
        "description": (
            "Vendors (suppliers) share the same res.partner model as customers. "
            "The supplier_rank field marks a contact as a vendor."
        ),
        "tips": (
            "Vendor pricelists are managed through purchase agreements and "
            "supplierinfo records on products."
        ),
    },
    "supplier": {
        "model": "res.partner",
        "filter": [["supplier_rank", ">", 0]],
        "description": "Alias for vendor. Same model and filter as 'vendor'.",
        "tips": "In Odoo 18, the preferred UI term is 'vendor' but supplier_rank is the technical field.",
    },
    "contact": {
        "model": "res.partner",
        "filter": [],
        "description": (
            "A generic contact entry — can be a customer, vendor, employee "
            "address, or any person/company you interact with."
        ),
        "tips": (
            "Contacts can have child contacts (type='contact', 'invoice', "
            "'delivery') for multi-address setups."
        ),
    },
    "company": {
        "model": "res.partner",
        "filter": [["is_company", "=", True]],
        "description": "Companies are contacts with is_company=True.",
        "tips": "Child contacts represent employees or departments within the company.",
    },
    "employee": {
        "model": "hr.employee",
        "filter": [],
        "description": (
            "Employee records in HR. Linked to a res.partner and optionally "
            "a res.users account for system access."
        ),
        "tips": (
            "Use hr.employee.public for limited public info. "
            "The related user_id field links to the Odoo user account."
        ),
    },
    "department": {
        "model": "hr.department",
        "filter": [],
        "description": "Organizational departments grouping employees.",
        "tips": "Departments have a parent_id for hierarchical org charts.",
    },
    "user": {
        "model": "res.users",
        "filter": [],
        "description": (
            "Odoo system users who can log in. Each user is linked to a "
            "res.partner record and has security groups for access control."
        ),
        "tips": (
            "Use groups_id to assign security groups. "
            "Internal users vs. portal users are distinguished by group membership."
        ),
    },

    # ── Sales ─────────────────────────────────────────────────────
    "sales order": {
        "model": "sale.order",
        "filter": [["state", "in", ["sale", "done"]]],
        "description": (
            "Confirmed sales orders. A sale.order starts as a quotation "
            "and becomes a sales order once confirmed."
        ),
        "tips": "state='draft' is a quotation, state='sale' is confirmed, state='done' is locked.",
    },
    "quotation": {
        "model": "sale.order",
        "filter": [["state", "=", "draft"]],
        "description": "Draft sales orders are quotations not yet confirmed by the customer.",
        "tips": "Quotations and sales orders are the same model — only the state differs.",
    },
    "order line": {
        "model": "sale.order.line",
        "filter": [],
        "description": "Individual line items on a sales order, each representing a product and quantity.",
        "tips": "price_unit, product_uom_qty, and discount are the main pricing fields.",
    },

    # ── Purchasing ────────────────────────────────────────────────
    "purchase order": {
        "model": "purchase.order",
        "filter": [["state", "in", ["purchase", "done"]]],
        "description": "Confirmed purchase orders sent to vendors.",
        "tips": "state='draft' is an RFQ, state='purchase' is a confirmed PO.",
    },
    "rfq": {
        "model": "purchase.order",
        "filter": [["state", "=", "draft"]],
        "description": "Request for Quotation — a draft purchase order awaiting vendor response.",
        "tips": "RFQ and PO are the same model (purchase.order), distinguished by state.",
    },

    # ── Accounting ────────────────────────────────────────────────
    "invoice": {
        "model": "account.move",
        "filter": [["move_type", "=", "out_invoice"]],
        "description": (
            "Customer invoices. In Odoo 18 all accounting entries use "
            "account.move — the move_type field distinguishes invoices, "
            "bills, and journal entries."
        ),
        "tips": (
            "move_type values: out_invoice (customer invoice), "
            "out_refund (credit note), in_invoice (vendor bill), "
            "in_refund (vendor credit note), entry (journal entry)."
        ),
    },
    "bill": {
        "model": "account.move",
        "filter": [["move_type", "=", "in_invoice"]],
        "description": "Vendor bills — invoices received from suppliers.",
        "tips": "Bills and invoices are the same model; only move_type differs.",
    },
    "credit note": {
        "model": "account.move",
        "filter": [["move_type", "in", ["out_refund", "in_refund"]]],
        "description": "Refund documents — out_refund for customers, in_refund for vendors.",
        "tips": "Create credit notes using the 'Add Credit Note' button on posted invoices/bills.",
    },
    "payment": {
        "model": "account.payment",
        "filter": [],
        "description": "Payment records for customer receipts and vendor payments.",
        "tips": (
            "Payments are linked to invoices/bills through reconciliation. "
            "payment_type='inbound' for customer payments, 'outbound' for vendor payments."
        ),
    },
    "journal": {
        "model": "account.journal",
        "filter": [],
        "description": (
            "Accounting journals — Sales, Purchase, Bank, Cash, and "
            "Miscellaneous. Every accounting entry belongs to a journal."
        ),
        "tips": "type values: sale, purchase, bank, cash, general.",
    },
    "account": {
        "model": "account.account",
        "filter": [],
        "description": "Chart of accounts entries — assets, liabilities, equity, income, expense accounts.",
        "tips": "account_type field classifies accounts (asset_receivable, liability_payable, income, expense, etc.).",
    },
    "tax": {
        "model": "account.tax",
        "filter": [],
        "description": "Tax definitions applied to invoices, bills, and sales/purchase orders.",
        "tips": (
            "type_tax_use: 'sale' for customer taxes, 'purchase' for vendor taxes, "
            "'none' for special taxes."
        ),
    },

    # ── Products ──────────────────────────────────────────────────
    "product": {
        "model": "product.template",
        "filter": [],
        "description": (
            "Product templates — the main product definition. Each template "
            "can have multiple variants based on attributes (size, color, etc.)."
        ),
        "tips": (
            "Use product.template for the catalog view. "
            "product.product represents specific variants. "
            "type='consu' for consumable, 'service' for service, 'product' for storable."
        ),
    },
    "product variant": {
        "model": "product.product",
        "filter": [],
        "description": (
            "Specific product variants — e.g., 'T-Shirt (Red, Large)'. "
            "Each variant belongs to a product.template."
        ),
        "tips": "product.product inherits from product.template. Most operations use product.product.",
    },
    "product category": {
        "model": "product.category",
        "filter": [],
        "description": "Hierarchical product categories for organizing the catalog.",
        "tips": (
            "Categories also control accounting properties (income/expense accounts) "
            "and costing methods."
        ),
    },
    "price list": {
        "model": "product.pricelist",
        "filter": [],
        "description": "Pricelists define pricing rules — discounts, formulas, and currency-based pricing.",
        "tips": "Pricelists can be assigned to customers, countries, or sales channels.",
    },

    # ── Inventory ─────────────────────────────────────────────────
    "warehouse": {
        "model": "stock.warehouse",
        "filter": [],
        "description": "Physical or logical warehouses with defined routes for receipts, deliveries, and internal moves.",
        "tips": "Each warehouse auto-creates input, output, and stock locations.",
    },
    "stock location": {
        "model": "stock.location",
        "filter": [],
        "description": "Inventory locations within warehouses — shelves, bins, zones, virtual locations.",
        "tips": "usage types: internal, transit, customer, supplier, production, inventory.",
    },
    "delivery order": {
        "model": "stock.picking",
        "filter": [["picking_type_code", "=", "outgoing"]],
        "description": "Outgoing shipments to customers. Created automatically from confirmed sales orders.",
        "tips": "state flow: draft -> waiting -> confirmed -> assigned -> done.",
    },
    "receipt": {
        "model": "stock.picking",
        "filter": [["picking_type_code", "=", "incoming"]],
        "description": "Incoming receipts from vendors. Created automatically from confirmed purchase orders.",
        "tips": "Validate the receipt to update stock quantities.",
    },
    "stock move": {
        "model": "stock.move",
        "filter": [],
        "description": "Individual product movements between locations — the atomic unit of inventory operations.",
        "tips": "Each picking contains one or more stock.move records.",
    },

    # ── Manufacturing ─────────────────────────────────────────────
    "bill of materials": {
        "model": "mrp.bom",
        "filter": [],
        "description": (
            "Bill of Materials — lists the components and quantities "
            "needed to manufacture a finished product."
        ),
        "tips": "type='normal' for standard manufacturing, 'phantom' for kit/set that explodes into components.",
    },
    "bom": {
        "model": "mrp.bom",
        "filter": [],
        "description": "Alias for Bill of Materials. See 'bill of materials'.",
        "tips": "type='normal' for manufacturing, 'phantom' for kits.",
    },
    "manufacturing order": {
        "model": "mrp.production",
        "filter": [],
        "description": "Production orders to manufacture products based on a BoM.",
        "tips": "state flow: draft -> confirmed -> progress -> to_close -> done.",
    },
    "work center": {
        "model": "mrp.workcenter",
        "filter": [],
        "description": "Physical production stations where work orders are performed.",
        "tips": "Track capacity, time efficiency, and costs per work center.",
    },
    "work order": {
        "model": "mrp.workorder",
        "filter": [],
        "description": "Individual production steps within a manufacturing order, assigned to a work center.",
        "tips": "Work orders follow the routing defined on the BoM.",
    },

    # ── CRM ───────────────────────────────────────────────────────
    "lead": {
        "model": "crm.lead",
        "filter": [["type", "=", "lead"]],
        "description": "Unqualified leads — initial contact or interest before qualification.",
        "tips": "Leads can be converted to opportunities with the 'Convert to Opportunity' action.",
    },
    "opportunity": {
        "model": "crm.lead",
        "filter": [["type", "=", "opportunity"]],
        "description": "Qualified sales opportunities tracked through pipeline stages.",
        "tips": "Leads and opportunities are the same model (crm.lead); type field distinguishes them.",
    },
    "pipeline stage": {
        "model": "crm.stage",
        "filter": [],
        "description": "Stages in the CRM pipeline (e.g., New, Qualified, Proposition, Won).",
        "tips": "is_won=True marks the stage as a winning stage for reporting.",
    },
    "sales team": {
        "model": "crm.team",
        "filter": [],
        "description": "Sales teams grouping salespeople for pipeline management and reporting.",
        "tips": "Teams can have their own pipelines, targets, and dashboards.",
    },

    # ── Project ───────────────────────────────────────────────────
    "project": {
        "model": "project.project",
        "filter": [],
        "description": "Project containers for organizing tasks, tracking progress, and managing teams.",
        "tips": "Enable timesheets, subtasks, and recurring tasks per project.",
    },
    "task": {
        "model": "project.task",
        "filter": [],
        "description": "Individual work items within a project, tracked on a Kanban board.",
        "tips": "user_ids (Many2many) assigns multiple users. stage_id controls Kanban column.",
    },
    "task stage": {
        "model": "project.task.type",
        "filter": [],
        "description": "Kanban stages for project tasks (e.g., To Do, In Progress, Done).",
        "tips": "Stages can be shared across projects or project-specific.",
    },

    # ── HR ────────────────────────────────────────────────────────
    "leave request": {
        "model": "hr.leave",
        "filter": [],
        "description": "Employee time-off requests (vacation, sick leave, etc.).",
        "tips": "state flow: draft -> confirm -> validate1 -> validate (depends on approval mode).",
    },
    "expense": {
        "model": "hr.expense",
        "filter": [],
        "description": "Individual expense line items submitted by employees for reimbursement.",
        "tips": "Expenses are grouped into hr.expense.sheet for approval and payment.",
    },
    "job position": {
        "model": "hr.job",
        "filter": [],
        "description": "Job positions defined in the company (e.g., Sales Manager, Developer).",
        "tips": "Links to recruitment for tracking open positions and applicants.",
    },
    "applicant": {
        "model": "hr.applicant",
        "filter": [],
        "description": "Job applicants tracked through recruitment stages.",
        "tips": "Can be converted to employee once hired. stage_id tracks recruitment progress.",
    },

    # ── Point of Sale ─────────────────────────────────────────────
    "pos order": {
        "model": "pos.order",
        "filter": [],
        "description": "Orders created at the Point of Sale terminal.",
        "tips": "POS orders generate accounting entries when the session is closed.",
    },
    "pos session": {
        "model": "pos.session",
        "filter": [],
        "description": "A cashier session on a POS terminal — tracks opening/closing balances.",
        "tips": "Sessions must be closed to post journal entries and reconcile payments.",
    },

    # ── Common / Technical ────────────────────────────────────────
    "currency": {
        "model": "res.currency",
        "filter": [],
        "description": "Currency definitions with exchange rates.",
        "tips": "Active currencies are those with active=True. Exchange rates are in res.currency.rate.",
    },
    "country": {
        "model": "res.country",
        "filter": [],
        "description": "Country records used in addresses, taxes, and localization.",
        "tips": "Countries have associated states/provinces in res.country.state.",
    },
    "sequence": {
        "model": "ir.sequence",
        "filter": [],
        "description": "Auto-numbering sequences for documents (invoices, orders, etc.).",
        "tips": "Configure prefix, suffix, padding, and number increment.",
    },
    "attachment": {
        "model": "ir.attachment",
        "filter": [],
        "description": "File attachments stored on any record.",
        "tips": "res_model and res_id link the attachment to a specific record.",
    },
    "activity": {
        "model": "mail.activity",
        "filter": [],
        "description": "Scheduled activities (to-do, call, meeting) linked to any record.",
        "tips": "activity_type_id defines the kind of activity. date_deadline sets the due date.",
    },
    "email template": {
        "model": "mail.template",
        "filter": [],
        "description": "Email templates with Jinja2 placeholders for automated emails.",
        "tips": "Use {{ object.field_name }} syntax in the template body.",
    },
    "automated action": {
        "model": "base.automation",
        "filter": [],
        "description": (
            "Server-side automation rules triggered on record creation, "
            "update, deletion, or time-based conditions."
        ),
        "tips": (
            "trigger values: on_create, on_write, on_unlink, on_time, "
            "on_create_or_write. Actions can execute Python code, send email, etc."
        ),
    },
    "scheduled action": {
        "model": "ir.cron",
        "filter": [],
        "description": "Cron jobs — scheduled tasks that run at defined intervals.",
        "tips": "Set interval_number and interval_type (minutes, hours, days, weeks, months).",
    },
    "access rule": {
        "model": "ir.model.access",
        "filter": [],
        "description": "Model-level access control — defines CRUD permissions per security group.",
        "tips": "perm_read, perm_write, perm_create, perm_unlink are boolean permission flags.",
    },
    "record rule": {
        "model": "ir.rule",
        "filter": [],
        "description": "Row-level security rules — domain-based filters restricting which records a group can see.",
        "tips": "domain_force contains the filter expression. global rules apply to everyone.",
    },
    "security group": {
        "model": "res.groups",
        "filter": [],
        "description": "Security groups controlling feature access and menu visibility.",
        "tips": "Groups can inherit from parent groups via implied_ids.",
    },
    "bank account": {
        "model": "res.partner.bank",
        "filter": [],
        "description": "Bank account records linked to contacts for payments and direct debit.",
        "tips": "acc_number holds the IBAN or account number. bank_id links to res.bank.",
    },
    "lot": {
        "model": "stock.lot",
        "filter": [],
        "description": "Lot or serial number records for product traceability.",
        "tips": "Use tracking='lot' on the product for batch tracking, 'serial' for unique serial numbers.",
    },
    "unit of measure": {
        "model": "uom.uom",
        "filter": [],
        "description": "Units of measure (kg, litre, unit, dozen, etc.) used on products and transactions.",
        "tips": "UoMs belong to categories (uom.category). Conversions happen within the same category.",
    },
    "inventory adjustment": {
        "model": "stock.quant",
        "filter": [],
        "description": "Current stock levels per product per location. Adjustments modify these.",
        "tips": "Use inventory adjustment wizard or direct quant updates.",
        "module": "stock",
    },
    "web page": {
        "model": "website.page",
        "filter": [],
        "description": "A page on the Odoo website.",
        "tips": "Pages are created via the website builder or programmatically.",
        "module": "website",
    },
    "website menu": {
        "model": "website.menu",
        "filter": [],
        "description": "Navigation menu item on the website.",
        "tips": "Menus can be nested for dropdown navigation.",
        "module": "website",
    },
}
