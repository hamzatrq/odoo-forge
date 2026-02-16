# Phase 1: Domain Knowledge Layer — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add structured Odoo domain knowledge as MCP resources so Claude becomes an Odoo expert that speaks business language.

**Architecture:** YAML knowledge files in `src/odooforge/knowledge/` loaded by a `KnowledgeBase` class, exposed as MCP resources via `@mcp.resource()` decorators on `server.py`. No new dependencies — use Python's built-in `json` for serialization and keep knowledge as Python dicts in `.py` files (matching existing patterns in `knowledge.py` and `recipes.py`).

**Tech Stack:** Python 3.11+, FastMCP resources (`mcp.server.fastmcp`), pytest

---

## Overview

```
src/odooforge/knowledge/
├── __init__.py              (KnowledgeBase class — loads and serves all knowledge)
├── modules.py               (~200 module entries with business descriptions)
├── dictionary.py            (~150 business-to-model mappings)
├── patterns.py              (~30 data model patterns)
├── best_practices.py        (Odoo conventions)
└── blueprints/
    ├── __init__.py           (blueprint registry + loader)
    ├── bakery.py
    ├── restaurant.py
    ├── ecommerce.py
    ├── manufacturing.py
    ├── services.py
    ├── retail.py
    ├── healthcare.py
    ├── education.py
    └── real_estate.py
```

All knowledge is stored as Python dictionaries (not YAML) to avoid adding dependencies. This matches the existing patterns in `tools/knowledge.py` (MODULE_KNOWLEDGE dict) and `tools/recipes.py` (RECIPES dict).

---

### Task 1: Create KnowledgeBase loader with first test

**Files:**
- Create: `src/odooforge/knowledge/__init__.py` (replace empty file)
- Create: `tests/test_knowledge_base.py`

**Step 1: Write the failing test**

```python
# tests/test_knowledge_base.py
"""Tests for the KnowledgeBase loader."""

import pytest


class TestKnowledgeBase:
    def test_knowledge_base_loads(self):
        from odooforge.knowledge import KnowledgeBase
        kb = KnowledgeBase()
        assert kb is not None

    def test_has_modules(self):
        from odooforge.knowledge import KnowledgeBase
        kb = KnowledgeBase()
        modules = kb.get_modules()
        assert isinstance(modules, dict)
        assert len(modules) > 0

    def test_has_dictionary(self):
        from odooforge.knowledge import KnowledgeBase
        kb = KnowledgeBase()
        dictionary = kb.get_dictionary()
        assert isinstance(dictionary, dict)
        assert len(dictionary) > 0

    def test_has_patterns(self):
        from odooforge.knowledge import KnowledgeBase
        kb = KnowledgeBase()
        patterns = kb.get_patterns()
        assert isinstance(patterns, dict)
        assert len(patterns) > 0

    def test_has_best_practices(self):
        from odooforge.knowledge import KnowledgeBase
        kb = KnowledgeBase()
        bp = kb.get_best_practices()
        assert isinstance(bp, dict)
        assert "rules" in bp

    def test_has_blueprints(self):
        from odooforge.knowledge import KnowledgeBase
        kb = KnowledgeBase()
        blueprints = kb.list_blueprints()
        assert isinstance(blueprints, list)
        assert len(blueprints) > 0

    def test_get_blueprint_by_id(self):
        from odooforge.knowledge import KnowledgeBase
        kb = KnowledgeBase()
        blueprint = kb.get_blueprint("bakery")
        assert blueprint is not None
        assert "modules" in blueprint
        assert "models" in blueprint

    def test_get_unknown_blueprint_returns_none(self):
        from odooforge.knowledge import KnowledgeBase
        kb = KnowledgeBase()
        assert kb.get_blueprint("nonexistent") is None
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_knowledge_base.py -v`
Expected: FAIL — `KnowledgeBase` not defined

**Step 3: Write minimal KnowledgeBase skeleton**

```python
# src/odooforge/knowledge/__init__.py
"""OdooForge Knowledge Base — structured Odoo domain knowledge."""

from __future__ import annotations

from typing import Any


class KnowledgeBase:
    """Central loader for all Odoo domain knowledge.

    Aggregates modules, dictionary, patterns, best practices,
    and industry blueprints into a single queryable interface.
    """

    def __init__(self) -> None:
        from odooforge.knowledge.modules import MODULES
        from odooforge.knowledge.dictionary import DICTIONARY
        from odooforge.knowledge.patterns import PATTERNS
        from odooforge.knowledge.best_practices import BEST_PRACTICES
        from odooforge.knowledge.blueprints import BLUEPRINTS

        self._modules = MODULES
        self._dictionary = DICTIONARY
        self._patterns = PATTERNS
        self._best_practices = BEST_PRACTICES
        self._blueprints = BLUEPRINTS

    def get_modules(self) -> dict[str, Any]:
        return self._modules

    def get_dictionary(self) -> dict[str, Any]:
        return self._dictionary

    def get_patterns(self) -> dict[str, Any]:
        return self._patterns

    def get_best_practices(self) -> dict[str, Any]:
        return self._best_practices

    def list_blueprints(self) -> list[str]:
        return list(self._blueprints.keys())

    def get_blueprint(self, blueprint_id: str) -> dict[str, Any] | None:
        return self._blueprints.get(blueprint_id)
```

This will still fail because the sub-modules don't exist yet. We need stubs. Create them in Tasks 2-6.

**Step 4: Run test to verify it still fails (expected — sub-modules missing)**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_knowledge_base.py::TestKnowledgeBase::test_knowledge_base_loads -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'odooforge.knowledge.modules'`

**Step 5: Don't commit yet — continue to Task 2**

---

### Task 2: Create modules knowledge (`modules.py`)

**Files:**
- Create: `src/odooforge/knowledge/modules.py`
- Modify: `tests/test_knowledge_base.py` (add module-specific tests)

**Step 1: Add failing tests for module knowledge structure**

Add to `tests/test_knowledge_base.py`:

```python
class TestModulesKnowledge:
    def test_module_entry_structure(self):
        from odooforge.knowledge.modules import MODULES
        # Every entry must have these keys
        for key, mod in MODULES.items():
            assert "name" in mod, f"{key} missing 'name'"
            assert "business_description" in mod, f"{key} missing 'business_description'"
            assert "category" in mod, f"{key} missing 'category'"
            assert isinstance(mod.get("depends", []), list)

    def test_known_modules_present(self):
        from odooforge.knowledge.modules import MODULES
        essential = ["sale", "purchase", "account", "stock", "crm", "hr",
                     "project", "website", "point_of_sale", "mrp"]
        for mod in essential:
            assert mod in MODULES, f"Essential module '{mod}' missing"

    def test_module_has_business_description(self):
        from odooforge.knowledge.modules import MODULES
        sale = MODULES["sale"]
        # Business description should be non-technical
        assert len(sale["business_description"]) > 20
        # Should NOT contain technical Odoo jargon
        assert "ir.module" not in sale["business_description"].lower()

    def test_module_count_minimum(self):
        from odooforge.knowledge.modules import MODULES
        # We aim for ~200 but start with at least 30 core modules
        assert len(MODULES) >= 30
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_knowledge_base.py::TestModulesKnowledge -v`
Expected: FAIL — module not found

**Step 3: Create modules.py with core module catalog**

```python
# src/odooforge/knowledge/modules.py
"""Odoo 18 module catalog with business-language descriptions.

Each entry maps a technical module name to business-friendly metadata.
"""

from __future__ import annotations

MODULES: dict[str, dict] = {
    # ── Sales & CRM ──────────────────────────────────────────
    "sale": {
        "name": "Sales",
        "business_description": "Manage sales orders and quotations. Create quotes, send them to customers, and convert to invoices when confirmed.",
        "category": "sales",
        "depends": ["contacts", "account"],
        "business_needs": ["selling products", "quotations", "sales orders", "invoicing"],
    },
    "crm": {
        "name": "CRM",
        "business_description": "Track leads and opportunities through your sales pipeline. Manage customer relationships, schedule follow-ups, and forecast revenue.",
        "category": "sales",
        "depends": ["contacts", "mail"],
        "business_needs": ["lead tracking", "sales pipeline", "customer relationships", "follow-ups"],
    },
    "sale_crm": {
        "name": "Sales + CRM Integration",
        "business_description": "Connect your sales pipeline to quotations. Convert won opportunities directly into sales orders.",
        "category": "sales",
        "depends": ["sale", "crm"],
        "business_needs": ["pipeline to quote", "opportunity conversion"],
    },

    # ── Purchasing ───────────────────────────────────────────
    "purchase": {
        "name": "Purchase",
        "business_description": "Manage purchase orders and vendor relationships. Create RFQs, track deliveries, and handle vendor bills.",
        "category": "purchasing",
        "depends": ["contacts", "account"],
        "business_needs": ["buying products", "purchase orders", "vendor management", "procurement"],
    },

    # ── Accounting & Finance ─────────────────────────────────
    "account": {
        "name": "Invoicing / Accounting",
        "business_description": "Full accounting suite with invoicing, payments, bank reconciliation, and financial reports.",
        "category": "accounting",
        "depends": ["contacts"],
        "business_needs": ["invoicing", "payments", "accounting", "financial reports", "taxes"],
    },
    "account_payment": {
        "name": "Online Payments",
        "business_description": "Accept online payments from customers via payment providers like Stripe, PayPal, etc.",
        "category": "accounting",
        "depends": ["account", "payment"],
        "business_needs": ["online payments", "payment processing"],
    },

    # ── Inventory & Warehouse ────────────────────────────────
    "stock": {
        "name": "Inventory",
        "business_description": "Track inventory levels across warehouses. Manage receipts, deliveries, internal transfers, and stock adjustments.",
        "category": "inventory",
        "depends": ["product"],
        "business_needs": ["inventory tracking", "warehouse management", "stock levels", "deliveries"],
    },
    "stock_account": {
        "name": "Inventory Accounting",
        "business_description": "Automatic accounting entries for inventory movements. Track cost of goods sold and inventory valuation.",
        "category": "inventory",
        "depends": ["stock", "account"],
        "business_needs": ["inventory valuation", "cost tracking"],
    },
    "delivery": {
        "name": "Shipping",
        "business_description": "Configure shipping methods and carriers. Calculate shipping costs and print labels.",
        "category": "inventory",
        "depends": ["stock"],
        "business_needs": ["shipping", "delivery", "carriers", "shipping labels"],
    },

    # ── Manufacturing ────────────────────────────────────────
    "mrp": {
        "name": "Manufacturing",
        "business_description": "Manage production orders with bills of materials and work orders. Plan manufacturing and track production.",
        "category": "manufacturing",
        "depends": ["stock"],
        "business_needs": ["manufacturing", "production", "bills of materials", "work orders"],
    },
    "mrp_workorder": {
        "name": "Work Orders",
        "business_description": "Detailed work order management with work centers, routing, and shop floor tracking.",
        "category": "manufacturing",
        "depends": ["mrp"],
        "business_needs": ["work centers", "production routing", "shop floor"],
    },
    "quality_control": {
        "name": "Quality Control",
        "business_description": "Define quality checks and control points in your manufacturing and inventory processes.",
        "category": "manufacturing",
        "depends": ["stock"],
        "business_needs": ["quality checks", "quality control", "inspections"],
    },
    "maintenance": {
        "name": "Maintenance",
        "business_description": "Schedule and track equipment maintenance. Preventive and corrective maintenance requests.",
        "category": "manufacturing",
        "depends": [],
        "business_needs": ["equipment maintenance", "preventive maintenance"],
    },

    # ── Point of Sale ────────────────────────────────────────
    "point_of_sale": {
        "name": "Point of Sale",
        "business_description": "In-store sales terminal. Process transactions, accept payments, and manage cash registers.",
        "category": "pos",
        "depends": ["stock", "account"],
        "business_needs": ["in-store sales", "POS", "cash register", "retail checkout"],
    },
    "pos_restaurant": {
        "name": "Restaurant POS",
        "business_description": "Restaurant-specific POS features: table management, floor plans, split bills, and kitchen printing.",
        "category": "pos",
        "depends": ["point_of_sale"],
        "business_needs": ["restaurant", "table management", "kitchen orders", "floor plan"],
    },
    "pos_sale": {
        "name": "POS + Sales Integration",
        "business_description": "Link POS orders to sales orders. Allow sales orders to be fulfilled through the POS.",
        "category": "pos",
        "depends": ["point_of_sale", "sale"],
        "business_needs": ["POS sales orders"],
    },
    "loyalty": {
        "name": "Loyalty Programs",
        "business_description": "Customer loyalty and rewards programs. Points, gift cards, discount codes, and promotions.",
        "category": "pos",
        "depends": [],
        "business_needs": ["loyalty program", "rewards", "gift cards", "promotions", "discount codes"],
    },

    # ── Website & eCommerce ──────────────────────────────────
    "website": {
        "name": "Website Builder",
        "business_description": "Build and manage your business website with a drag-and-drop editor. Pages, menus, and themes.",
        "category": "website",
        "depends": [],
        "business_needs": ["website", "web pages", "online presence"],
    },
    "website_sale": {
        "name": "eCommerce",
        "business_description": "Online store with product catalog, shopping cart, checkout, and order management.",
        "category": "website",
        "depends": ["website", "sale"],
        "business_needs": ["online store", "ecommerce", "online selling", "shopping cart"],
    },
    "website_sale_stock": {
        "name": "eCommerce Inventory",
        "business_description": "Show real-time stock availability on your online store. Out-of-stock indicators.",
        "category": "website",
        "depends": ["website_sale", "stock"],
        "business_needs": ["online stock display", "availability"],
    },
    "website_sale_wishlist": {
        "name": "Wishlist",
        "business_description": "Let customers save products to a wishlist for later purchase.",
        "category": "website",
        "depends": ["website_sale"],
        "business_needs": ["wishlist", "save for later"],
    },
    "website_sale_comparison": {
        "name": "Product Comparison",
        "business_description": "Let customers compare product features side by side on your online store.",
        "category": "website",
        "depends": ["website_sale"],
        "business_needs": ["product comparison"],
    },
    "payment": {
        "name": "Payment Providers",
        "business_description": "Configure payment providers (Stripe, PayPal, etc.) for online and invoice payments.",
        "category": "website",
        "depends": [],
        "business_needs": ["payment processing", "Stripe", "PayPal", "online payments"],
    },

    # ── HR & Employees ───────────────────────────────────────
    "hr": {
        "name": "Employees",
        "business_description": "Core employee records — departments, job positions, contact info, and org chart.",
        "category": "hr",
        "depends": [],
        "business_needs": ["employee management", "HR", "departments", "org chart"],
    },
    "hr_holidays": {
        "name": "Time Off",
        "business_description": "Manage employee leave requests — vacation, sick days, personal time. Approval workflows.",
        "category": "hr",
        "depends": ["hr"],
        "business_needs": ["time off", "leave management", "vacation", "sick days"],
    },
    "hr_attendance": {
        "name": "Attendance",
        "business_description": "Track employee check-in and check-out times. Attendance reports.",
        "category": "hr",
        "depends": ["hr"],
        "business_needs": ["attendance", "check-in", "time tracking"],
    },
    "hr_expense": {
        "name": "Expenses",
        "business_description": "Employee expense reporting and reimbursement. Submit expenses, approval workflow, and accounting integration.",
        "category": "hr",
        "depends": ["hr", "account"],
        "business_needs": ["expenses", "reimbursement", "expense reports"],
    },
    "hr_recruitment": {
        "name": "Recruitment",
        "business_description": "Manage job postings, applications, and hiring pipeline. Track candidates through interview stages.",
        "category": "hr",
        "depends": ["hr"],
        "business_needs": ["hiring", "recruitment", "job postings", "candidates"],
    },
    "hr_timesheet": {
        "name": "Timesheets",
        "business_description": "Track time spent on projects and tasks. Used for billing and productivity analysis.",
        "category": "hr",
        "depends": ["hr", "project"],
        "business_needs": ["timesheets", "time tracking", "billable hours"],
    },

    # ── Project Management ───────────────────────────────────
    "project": {
        "name": "Project Management",
        "business_description": "Manage projects with tasks, stages, and deadlines. Kanban boards, Gantt charts, and team collaboration.",
        "category": "project",
        "depends": ["mail"],
        "business_needs": ["projects", "tasks", "project management", "kanban", "deadlines"],
    },
    "sale_timesheet": {
        "name": "Billable Time",
        "business_description": "Bill customers based on time spent on their projects. Connect timesheets to sales orders.",
        "category": "project",
        "depends": ["sale", "hr_timesheet"],
        "business_needs": ["billable time", "time billing", "service invoicing"],
    },

    # ── Communication ────────────────────────────────────────
    "mail": {
        "name": "Discuss / Email",
        "business_description": "Internal messaging, email integration, and activity tracking across all records.",
        "category": "communication",
        "depends": [],
        "business_needs": ["messaging", "email", "internal communication", "notifications"],
    },
    "calendar": {
        "name": "Calendar",
        "business_description": "Shared calendar for meetings, appointments, and events. Sync with Google/Outlook calendars.",
        "category": "communication",
        "depends": ["mail"],
        "business_needs": ["calendar", "meetings", "appointments", "scheduling"],
    },

    # ── Contacts ─────────────────────────────────────────────
    "contacts": {
        "name": "Contacts",
        "business_description": "Manage your contacts database — customers, vendors, and companies with addresses and communication history.",
        "category": "contacts",
        "depends": ["mail"],
        "business_needs": ["contacts", "address book", "customers", "vendors"],
    },

    # ── Product ──────────────────────────────────────────────
    "product": {
        "name": "Products",
        "business_description": "Product catalog management — products, variants, pricing, categories, and attributes.",
        "category": "product",
        "depends": [],
        "business_needs": ["products", "product catalog", "pricing", "variants"],
    },
}
```

**Step 4: Run test to verify it passes (modules tests only — full KB still missing other modules)**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_knowledge_base.py::TestModulesKnowledge -v`
Expected: PASS

**Step 5: Don't commit yet — continue to Task 3**

---

### Task 3: Create business dictionary (`dictionary.py`)

**Files:**
- Create: `src/odooforge/knowledge/dictionary.py`
- Modify: `tests/test_knowledge_base.py`

**Step 1: Add failing tests**

Add to `tests/test_knowledge_base.py`:

```python
class TestDictionaryKnowledge:
    def test_dictionary_structure(self):
        from odooforge.knowledge.dictionary import DICTIONARY
        for term, mapping in DICTIONARY.items():
            assert "model" in mapping, f"'{term}' missing 'model'"
            assert "description" in mapping, f"'{term}' missing 'description'"

    def test_common_business_terms(self):
        from odooforge.knowledge.dictionary import DICTIONARY
        essential = ["customer", "vendor", "invoice", "product",
                     "sales order", "employee", "warehouse"]
        for term in essential:
            assert term in DICTIONARY, f"Business term '{term}' missing"

    def test_dictionary_count_minimum(self):
        from odooforge.knowledge.dictionary import DICTIONARY
        assert len(DICTIONARY) >= 40
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_knowledge_base.py::TestDictionaryKnowledge -v`
Expected: FAIL

**Step 3: Create dictionary.py**

```python
# src/odooforge/knowledge/dictionary.py
"""Business-to-Odoo dictionary — maps business terms to Odoo models and concepts."""

from __future__ import annotations

DICTIONARY: dict[str, dict] = {
    # ── People ───────────────────────────────────────────────
    "customer": {
        "model": "res.partner",
        "filter": [["customer_rank", ">", 0]],
        "description": "Customers are stored in the contacts model (res.partner) with customer_rank > 0.",
        "tips": "Use is_company=True for companies, False for individuals.",
    },
    "vendor": {
        "model": "res.partner",
        "filter": [["supplier_rank", ">", 0]],
        "description": "Vendors/suppliers are contacts with supplier_rank > 0.",
        "tips": "A contact can be both a customer and vendor.",
    },
    "supplier": {
        "model": "res.partner",
        "filter": [["supplier_rank", ">", 0]],
        "description": "Same as vendor — contacts with supplier_rank > 0.",
        "tips": "Alias for vendor.",
    },
    "contact": {
        "model": "res.partner",
        "description": "All people and companies — customers, vendors, employees' contacts.",
    },
    "company": {
        "model": "res.company",
        "description": "Your own company/companies. Odoo supports multi-company setups.",
    },
    "employee": {
        "model": "hr.employee",
        "description": "Employee records linked to contacts. Requires HR module.",
        "module": "hr",
    },
    "department": {
        "model": "hr.department",
        "description": "Organizational departments for grouping employees.",
        "module": "hr",
    },
    "user": {
        "model": "res.users",
        "description": "System users who can log into Odoo. Linked to contacts.",
    },

    # ── Sales ────────────────────────────────────────────────
    "sales order": {
        "model": "sale.order",
        "description": "A confirmed quotation that becomes a sales order.",
        "module": "sale",
    },
    "quotation": {
        "model": "sale.order",
        "filter": [["state", "in", ["draft", "sent"]]],
        "description": "A draft or sent sales order is called a quotation.",
        "module": "sale",
    },
    "order line": {
        "model": "sale.order.line",
        "description": "Individual line items on a sales order.",
        "module": "sale",
    },

    # ── Purchasing ───────────────────────────────────────────
    "purchase order": {
        "model": "purchase.order",
        "description": "An order to buy products from a vendor.",
        "module": "purchase",
    },
    "rfq": {
        "model": "purchase.order",
        "filter": [["state", "=", "draft"]],
        "description": "A Request for Quotation — a draft purchase order sent to a vendor.",
        "module": "purchase",
    },

    # ── Accounting ───────────────────────────────────────────
    "invoice": {
        "model": "account.move",
        "filter": [["move_type", "=", "out_invoice"]],
        "description": "Customer invoices. In Odoo, invoices are a type of account.move.",
        "module": "account",
    },
    "bill": {
        "model": "account.move",
        "filter": [["move_type", "=", "in_invoice"]],
        "description": "Vendor bills (incoming invoices). Also account.move records.",
        "module": "account",
    },
    "credit note": {
        "model": "account.move",
        "filter": [["move_type", "in", ["out_refund", "in_refund"]]],
        "description": "Refund documents — out_refund for customers, in_refund for vendors.",
        "module": "account",
    },
    "payment": {
        "model": "account.payment",
        "description": "Customer or vendor payment records.",
        "module": "account",
    },
    "journal": {
        "model": "account.journal",
        "description": "Accounting journals — bank, cash, sales, purchase, miscellaneous.",
        "module": "account",
    },
    "account": {
        "model": "account.account",
        "description": "Chart of accounts entries — revenue, expense, asset, liability accounts.",
        "module": "account",
    },
    "tax": {
        "model": "account.tax",
        "description": "Tax definitions — VAT, sales tax, etc.",
        "module": "account",
    },

    # ── Products ─────────────────────────────────────────────
    "product": {
        "model": "product.template",
        "description": "Product templates — the main product record. Use product.product for specific variants.",
        "tips": "product.template is the parent, product.product is the variant. Most operations use product.template.",
    },
    "product variant": {
        "model": "product.product",
        "description": "Specific product variants (e.g., T-shirt in size L, color Blue).",
    },
    "product category": {
        "model": "product.category",
        "description": "Hierarchical product categorization.",
    },
    "price list": {
        "model": "product.pricelist",
        "description": "Pricing rules for different customer segments, quantities, or periods.",
    },

    # ── Inventory ────────────────────────────────────────────
    "warehouse": {
        "model": "stock.warehouse",
        "description": "Physical warehouse locations with incoming/outgoing/internal operation types.",
        "module": "stock",
    },
    "stock location": {
        "model": "stock.location",
        "description": "Specific locations within a warehouse (shelves, zones, virtual locations).",
        "module": "stock",
    },
    "delivery order": {
        "model": "stock.picking",
        "filter": [["picking_type_code", "=", "outgoing"]],
        "description": "Outgoing shipments to customers.",
        "module": "stock",
    },
    "receipt": {
        "model": "stock.picking",
        "filter": [["picking_type_code", "=", "incoming"]],
        "description": "Incoming shipments from vendors.",
        "module": "stock",
    },
    "inventory adjustment": {
        "model": "stock.quant",
        "description": "Current stock levels per product per location. Adjustments modify these.",
        "module": "stock",
    },
    "stock move": {
        "model": "stock.move",
        "description": "Individual product movement between locations.",
        "module": "stock",
    },

    # ── Manufacturing ────────────────────────────────────────
    "bill of materials": {
        "model": "mrp.bom",
        "description": "Recipe/formula for manufacturing a product — lists components and quantities.",
        "module": "mrp",
    },
    "bom": {
        "model": "mrp.bom",
        "description": "Alias for bill of materials.",
        "module": "mrp",
    },
    "manufacturing order": {
        "model": "mrp.production",
        "description": "A production order to manufacture products using a bill of materials.",
        "module": "mrp",
    },
    "work center": {
        "model": "mrp.workcenter",
        "description": "A machine or station where manufacturing operations happen.",
        "module": "mrp",
    },
    "work order": {
        "model": "mrp.workorder",
        "description": "Individual operations within a manufacturing order, assigned to work centers.",
        "module": "mrp",
    },

    # ── CRM ──────────────────────────────────────────────────
    "lead": {
        "model": "crm.lead",
        "filter": [["type", "=", "lead"]],
        "description": "An unqualified prospect. Converted to an opportunity when qualified.",
        "module": "crm",
    },
    "opportunity": {
        "model": "crm.lead",
        "filter": [["type", "=", "opportunity"]],
        "description": "A qualified sales opportunity in the pipeline. Same model as lead.",
        "module": "crm",
    },
    "pipeline stage": {
        "model": "crm.stage",
        "description": "Stages in the CRM pipeline (New, Qualified, Proposition, Won).",
        "module": "crm",
    },
    "sales team": {
        "model": "crm.team",
        "description": "Group of salespeople with shared pipeline and targets.",
        "module": "crm",
    },

    # ── Project ──────────────────────────────────────────────
    "project": {
        "model": "project.project",
        "description": "A project container for tasks. Has stages, team members, and deadlines.",
        "module": "project",
    },
    "task": {
        "model": "project.task",
        "description": "Individual work items within a project.",
        "module": "project",
    },
    "task stage": {
        "model": "project.task.type",
        "description": "Task stages (To Do, In Progress, Done). Shared across projects or per-project.",
        "module": "project",
    },

    # ── HR ───────────────────────────────────────────────────
    "leave request": {
        "model": "hr.leave",
        "description": "Employee time-off request (vacation, sick day, etc.).",
        "module": "hr_holidays",
    },
    "expense": {
        "model": "hr.expense",
        "description": "Employee expense report line item.",
        "module": "hr_expense",
    },
    "job position": {
        "model": "hr.job",
        "description": "Job titles/positions in the organization.",
        "module": "hr",
    },
    "applicant": {
        "model": "hr.applicant",
        "description": "Job candidate/applicant in the recruitment pipeline.",
        "module": "hr_recruitment",
    },

    # ── POS ──────────────────────────────────────────────────
    "pos order": {
        "model": "pos.order",
        "description": "A point-of-sale transaction/order.",
        "module": "point_of_sale",
    },
    "pos session": {
        "model": "pos.session",
        "description": "A POS cashier session — opened when starting work, closed at end of shift.",
        "module": "point_of_sale",
    },

    # ── Website ──────────────────────────────────────────────
    "web page": {
        "model": "website.page",
        "description": "A page on the Odoo website.",
        "module": "website",
    },
    "website menu": {
        "model": "website.menu",
        "description": "Navigation menu item on the website.",
        "module": "website",
    },

    # ── Other Common ─────────────────────────────────────────
    "currency": {
        "model": "res.currency",
        "description": "Currencies with exchange rates.",
    },
    "country": {
        "model": "res.country",
        "description": "Country records used in addresses and localization.",
    },
    "sequence": {
        "model": "ir.sequence",
        "description": "Auto-incrementing number sequences (SO001, INV001, etc.).",
    },
    "attachment": {
        "model": "ir.attachment",
        "description": "File attachments linked to any record.",
    },
    "activity": {
        "model": "mail.activity",
        "description": "Scheduled follow-up activities (to-do, call, meeting) on any record.",
    },
    "email template": {
        "model": "mail.template",
        "description": "Reusable email templates with dynamic placeholders.",
    },
    "automated action": {
        "model": "base.automation",
        "description": "Server-side automation rules triggered by record events.",
    },
    "scheduled action": {
        "model": "ir.cron",
        "description": "Recurring scheduled jobs (cron jobs) that run automatically.",
    },
    "access rule": {
        "model": "ir.model.access",
        "description": "Model-level access rights (CRUD) per security group.",
    },
    "record rule": {
        "model": "ir.rule",
        "description": "Row-level access rules — who can see/edit which records.",
    },
    "security group": {
        "model": "res.groups",
        "description": "User groups that control access to features and data.",
    },
}
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_knowledge_base.py::TestDictionaryKnowledge -v`
Expected: PASS

**Step 5: Don't commit yet — continue to Task 4**

---

### Task 4: Create patterns knowledge (`patterns.py`)

**Files:**
- Create: `src/odooforge/knowledge/patterns.py`
- Modify: `tests/test_knowledge_base.py`

**Step 1: Add failing tests**

Add to `tests/test_knowledge_base.py`:

```python
class TestPatternsKnowledge:
    def test_pattern_structure(self):
        from odooforge.knowledge.patterns import PATTERNS
        for key, pattern in PATTERNS.items():
            assert "name" in pattern, f"'{key}' missing 'name'"
            assert "description" in pattern, f"'{key}' missing 'description'"
            assert "approach" in pattern, f"'{key}' missing 'approach'"
            assert pattern["approach"] in ("configuration", "code_generation", "either")
            assert "ingredients" in pattern, f"'{key}' missing 'ingredients'"

    def test_known_patterns_present(self):
        from odooforge.knowledge.patterns import PATTERNS
        expected = ["partner_extension", "trackable_custom_model",
                    "product_extension", "multi_company_model"]
        for p in expected:
            assert p in PATTERNS, f"Pattern '{p}' missing"

    def test_pattern_count_minimum(self):
        from odooforge.knowledge.patterns import PATTERNS
        assert len(PATTERNS) >= 10
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_knowledge_base.py::TestPatternsKnowledge -v`
Expected: FAIL

**Step 3: Create patterns.py**

```python
# src/odooforge/knowledge/patterns.py
"""Data model patterns — common Odoo customization recipes."""

from __future__ import annotations

PATTERNS: dict[str, dict] = {
    "partner_extension": {
        "name": "Extend Contacts",
        "description": "Add custom fields to customers/companies (res.partner).",
        "approach": "configuration",
        "when_to_use": "Adding custom data to contacts — loyalty tiers, industry codes, preferences.",
        "ingredients": [
            "Custom x_ fields on res.partner via schema tools",
            "Form view inheritance via XPath to show new fields",
            "Optional: tree/kanban view updates",
            "Optional: search filter for new fields",
        ],
        "example_fields": [
            {"name": "x_loyalty_tier", "type": "selection", "options": "bronze,silver,gold"},
            {"name": "x_industry_code", "type": "char"},
            {"name": "x_preferred_contact_method", "type": "selection", "options": "email,phone,whatsapp"},
        ],
    },
    "product_extension": {
        "name": "Extend Products",
        "description": "Add custom fields to products (product.template).",
        "approach": "configuration",
        "when_to_use": "Adding product-specific data — allergens, prep time, custom specs.",
        "ingredients": [
            "Custom x_ fields on product.template",
            "Form view inheritance",
            "Optional: website display via website_sale view inheritance",
        ],
        "example_fields": [
            {"name": "x_allergens", "type": "many2many"},
            {"name": "x_prep_time_minutes", "type": "integer"},
            {"name": "x_is_made_to_order", "type": "boolean"},
        ],
    },
    "trackable_custom_model": {
        "name": "Trackable Custom Model",
        "description": "A new model with messaging, activity tracking, and stage-based workflow.",
        "approach": "code_generation",
        "when_to_use": "Creating entirely new business objects — warranty claims, inspection records, custom tickets.",
        "ingredients": [
            "New model inheriting mail.thread + mail.activity.mixin",
            "name (Char) + active (Boolean) fields",
            "stage_id (Many2one) to a stage model for kanban workflow",
            "Form, tree, and kanban views",
            "Menu item under appropriate app",
            "Security: ir.model.access for user/manager groups",
        ],
        "requires_code": True,
    },
    "simple_custom_model": {
        "name": "Simple Custom Model",
        "description": "A basic new model without mail integration — for reference data or simple records.",
        "approach": "configuration",
        "when_to_use": "Creating lookup tables, tag models, or simple reference data.",
        "ingredients": [
            "New model via odoo_schema_model_create",
            "name (Char) field",
            "Optional: sequence (Integer) for ordering",
            "Tree + form views",
        ],
    },
    "multi_company_model": {
        "name": "Multi-Company Data Isolation",
        "description": "Add multi-company support to custom models or extend existing ones.",
        "approach": "code_generation",
        "when_to_use": "When data must be isolated between companies in a multi-company setup.",
        "ingredients": [
            "company_id (Many2one to res.company) field with default=lambda self: self.env.company",
            "Record rule (ir.rule) with domain [('company_id', 'in', company_ids)]",
            "Form view showing company_id field",
        ],
    },
    "smart_button": {
        "name": "Smart Button on Form",
        "description": "Add a count/link button on a form view pointing to related records.",
        "approach": "code_generation",
        "when_to_use": "Showing related record counts — e.g., 'Orders: 5' button on partner form.",
        "ingredients": [
            "Computed field for count (e.g., order_count = fields.Integer(compute='_compute_order_count'))",
            "Action window for the related model with domain filter",
            "Button element in form view's button_box",
        ],
    },
    "automated_workflow": {
        "name": "Automated Workflow",
        "description": "Trigger actions when records change — send emails, update fields, create records.",
        "approach": "configuration",
        "when_to_use": "Automating repetitive tasks — welcome emails, status updates, notifications.",
        "ingredients": [
            "base.automation rule via odoo_automation_create",
            "Trigger: on_create, on_write, on_unlink, or timed",
            "Action: email, update fields, execute Python code, or create activity",
            "Optional: email template via odoo_email_template_create",
        ],
    },
    "custom_report": {
        "name": "Custom PDF Report",
        "description": "Create or customize a printable PDF report (invoices, packing slips, etc.).",
        "approach": "configuration",
        "when_to_use": "Custom invoice layouts, packing slips, certificates, or any printable document.",
        "ingredients": [
            "QWeb template via odoo_report_modify or odoo_report_get_template",
            "Report action linking template to model",
            "Paper format configuration (optional)",
        ],
    },
    "kanban_workflow": {
        "name": "Kanban Stage Workflow",
        "description": "Stage-based workflow with drag-and-drop kanban board.",
        "approach": "either",
        "when_to_use": "Any process with defined stages — support tickets, hiring pipeline, order processing.",
        "ingredients": [
            "Stage model with name + sequence fields",
            "stage_id Many2one field on the main model",
            "Kanban view with default_group_by='stage_id'",
            "Optional: automated actions on stage transitions",
        ],
    },
    "approval_workflow": {
        "name": "Approval Workflow",
        "description": "Multi-step approval process with state transitions.",
        "approach": "code_generation",
        "when_to_use": "Purchase approvals, leave requests, expense reports — anything needing sign-off.",
        "ingredients": [
            "state Selection field (draft, submitted, approved, rejected)",
            "Button methods for state transitions",
            "Group-based access to approve/reject",
            "Automated notifications on state change",
        ],
    },
    "data_import_pipeline": {
        "name": "Data Import Pipeline",
        "description": "Import data from CSV/external sources into Odoo.",
        "approach": "configuration",
        "when_to_use": "Migrating data from spreadsheets, other ERPs, or external systems.",
        "ingredients": [
            "odoo_import_preview to validate CSV mapping",
            "odoo_import_execute to run the import",
            "odoo_import_template to generate CSV template",
            "Snapshot before import for safety",
        ],
    },
    "scheduled_job": {
        "name": "Scheduled Recurring Job",
        "description": "Automated task that runs on a schedule (daily, weekly, etc.).",
        "approach": "code_generation",
        "when_to_use": "Recurring cleanup, sync with external systems, periodic reports.",
        "ingredients": [
            "ir.cron record with interval configuration",
            "Python method on the target model",
            "Error handling and logging",
        ],
    },
    "website_controller": {
        "name": "Custom Web Endpoint",
        "description": "Custom HTTP routes for API endpoints or custom web pages.",
        "approach": "code_generation",
        "when_to_use": "External integrations, webhooks, custom landing pages, REST APIs.",
        "ingredients": [
            "http.Controller class with @http.route decorators",
            "JSON or HTTP response handling",
            "Authentication: public, user, or API key",
        ],
    },
}
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_knowledge_base.py::TestPatternsKnowledge -v`
Expected: PASS

**Step 5: Don't commit yet — continue to Task 5**

---

### Task 5: Create best practices knowledge (`best_practices.py`)

**Files:**
- Create: `src/odooforge/knowledge/best_practices.py`
- Modify: `tests/test_knowledge_base.py`

**Step 1: Add failing tests**

Add to `tests/test_knowledge_base.py`:

```python
class TestBestPracticesKnowledge:
    def test_best_practices_structure(self):
        from odooforge.knowledge.best_practices import BEST_PRACTICES
        assert "rules" in BEST_PRACTICES
        assert isinstance(BEST_PRACTICES["rules"], list)
        assert len(BEST_PRACTICES["rules"]) >= 10

    def test_rule_structure(self):
        from odooforge.knowledge.best_practices import BEST_PRACTICES
        for rule in BEST_PRACTICES["rules"]:
            assert "category" in rule
            assert "rule" in rule
            assert "why" in rule
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_knowledge_base.py::TestBestPracticesKnowledge -v`
Expected: FAIL

**Step 3: Create best_practices.py**

```python
# src/odooforge/knowledge/best_practices.py
"""Odoo best practices and conventions."""

from __future__ import annotations

BEST_PRACTICES: dict = {
    "rules": [
        # ── Naming ───────────────────────────────────────────
        {
            "category": "naming",
            "rule": "Custom fields must use x_ prefix",
            "why": "Odoo reserves non-prefixed field names for core modules. x_ ensures no conflicts during upgrades.",
            "example": "x_loyalty_tier, not loyalty_tier",
        },
        {
            "category": "naming",
            "rule": "Custom models must use x_ prefix",
            "why": "Same reason as fields — avoids namespace collisions with core and OCA modules.",
            "example": "x_bakery.loyalty_program",
        },
        {
            "category": "naming",
            "rule": "Model names use dots for namespacing, underscores for words",
            "why": "Convention: module.entity_name (e.g., sale.order, stock.picking).",
            "example": "x_bakery.loyalty_program (not x_bakery_loyalty_program)",
        },

        # ── Model Design ────────────────────────────────────
        {
            "category": "model_design",
            "rule": "Add mail.thread mixin to any record users will discuss",
            "why": "Enables the chatter (message log), email notifications, and followers.",
            "example": "_inherit = ['mail.thread', 'mail.activity.mixin']",
        },
        {
            "category": "model_design",
            "rule": "Include a 'name' Char field as the first field",
            "why": "Odoo uses _rec_name (defaults to 'name') for display. Without it, records show as IDs.",
            "example": "name = fields.Char(required=True)",
        },
        {
            "category": "model_design",
            "rule": "Add 'active' Boolean field with default True",
            "why": "Enables the archive/unarchive feature. Inactive records are hidden by default.",
            "example": "active = fields.Boolean(default=True)",
        },
        {
            "category": "model_design",
            "rule": "Use ir.sequence for human-readable reference numbers",
            "why": "Auto-generated IDs like SO001, INV001 are more user-friendly than database IDs.",
            "example": "ref = fields.Char(default=lambda self: self.env['ir.sequence'].next_by_code('my.model'))",
        },
        {
            "category": "model_design",
            "rule": "Add company_id field for multi-company isolation",
            "why": "Without it, records are shared across all companies — usually not desired.",
            "example": "company_id = fields.Many2one('res.company', default=lambda self: self.env.company)",
        },

        # ── Fields ───────────────────────────────────────────
        {
            "category": "fields",
            "rule": "Store computed fields that appear in search/filter/group_by",
            "why": "Non-stored computed fields can't be searched or grouped in the UI.",
            "example": "total = fields.Float(compute='_compute_total', store=True)",
        },
        {
            "category": "fields",
            "rule": "Use Selection for fixed options, Many2one for dynamic/extensible lists",
            "why": "Selection is simpler but hardcoded. Many2one allows users to add new options without code changes.",
            "example": "Use Many2one to a stage model instead of Selection for workflow states that users should customize.",
        },
        {
            "category": "fields",
            "rule": "Use Many2many through a relation table for large tag-like relationships",
            "why": "Default Many2many table naming can conflict. Explicit relation names prevent issues.",
            "example": "tag_ids = fields.Many2many('my.tag', 'my_model_tag_rel', 'model_id', 'tag_id')",
        },

        # ── Security ─────────────────────────────────────────
        {
            "category": "security",
            "rule": "Always create ir.model.access records for new models",
            "why": "Without access rules, no user (including admin in some cases) can access the model's records.",
            "example": "Create CSV: access_my_model_user,model_my_model,group_user,1,1,1,0",
        },
        {
            "category": "security",
            "rule": "Use record rules (ir.rule) for multi-company, not just access rules",
            "why": "Access rules control model-level CRUD. Record rules control which rows a user can see.",
            "example": "domain_force: ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]",
        },
        {
            "category": "security",
            "rule": "Create at least two groups: user and manager",
            "why": "Standard Odoo pattern. Users have basic CRUD, managers can configure and delete.",
            "example": "group_my_module_user, group_my_module_manager (implied_ids includes user)",
        },

        # ── Views ────────────────────────────────────────────
        {
            "category": "views",
            "rule": "Prefer view inheritance over replacing entire views",
            "why": "Inheritance preserves other customizations and is upgrade-safe.",
            "example": "Use XPath expressions to insert/replace specific elements.",
        },
        {
            "category": "views",
            "rule": "Group related fields in form views using <group> tags",
            "why": "Odoo's form layout uses groups for two-column layouts. Ungrouped fields look messy.",
            "example": "<group><group>Left fields</group><group>Right fields</group></group>",
        },
        {
            "category": "views",
            "rule": "Add search view with common filters and group_by options",
            "why": "Users expect to filter and group data. Without search view customization, they can't.",
            "example": "<filter name='my_filter' string='Active' domain=\"[('active','=',True)]\"/>",
        },

        # ── Automation ───────────────────────────────────────
        {
            "category": "automation",
            "rule": "Use server actions for simple automations, not Python code",
            "why": "Server actions are configurable without code deployment. Python code actions require module upgrades.",
            "example": "Use 'Update Record' action type instead of 'Execute Python Code' when possible.",
        },
        {
            "category": "automation",
            "rule": "Always test automations on a snapshot/copy of your database first",
            "why": "Misconfigured automations can update/delete many records at once. Test in isolation.",
            "example": "Create snapshot → test automation → verify → apply to production.",
        },

        # ── Reports ──────────────────────────────────────────
        {
            "category": "reports",
            "rule": "Use t-esc for user content, t-raw only for trusted HTML",
            "why": "t-raw renders raw HTML which is an XSS risk if the content comes from users.",
            "example": "<span t-esc=\"record.name\"/> (safe) vs <span t-raw=\"record.html_field\"/> (only for sanitized HTML)",
        },

        # ── Performance ──────────────────────────────────────
        {
            "category": "performance",
            "rule": "Avoid computed fields that trigger ORM queries in loops",
            "why": "N+1 query problem — each record triggers a separate query, causing slow page loads.",
            "example": "Use read_group or prefetch patterns instead of per-record queries.",
        },
        {
            "category": "performance",
            "rule": "Use read_group for dashboard/reporting aggregations",
            "why": "read_group translates to SQL GROUP BY — orders of magnitude faster than reading all records.",
            "example": "self.env['sale.order'].read_group(domain, ['amount_total'], ['partner_id'])",
        },
    ],
}
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_knowledge_base.py::TestBestPracticesKnowledge -v`
Expected: PASS

**Step 5: Don't commit yet — continue to Task 6**

---

### Task 6: Create blueprints package with bakery blueprint

**Files:**
- Create: `src/odooforge/knowledge/blueprints/__init__.py`
- Create: `src/odooforge/knowledge/blueprints/bakery.py`
- Modify: `tests/test_knowledge_base.py`

**Step 1: Add failing tests**

Add to `tests/test_knowledge_base.py`:

```python
class TestBlueprintsKnowledge:
    def test_blueprint_registry(self):
        from odooforge.knowledge.blueprints import BLUEPRINTS
        assert isinstance(BLUEPRINTS, dict)
        assert "bakery" in BLUEPRINTS

    def test_blueprint_structure(self):
        from odooforge.knowledge.blueprints import BLUEPRINTS
        for key, bp in BLUEPRINTS.items():
            assert "name" in bp, f"'{key}' missing 'name'"
            assert "description" in bp, f"'{key}' missing 'description'"
            assert "modules" in bp, f"'{key}' missing 'modules'"
            assert isinstance(bp["modules"], list)
            assert "models" in bp, f"'{key}' missing 'models'"
            assert isinstance(bp["models"], list)

    def test_bakery_blueprint_complete(self):
        from odooforge.knowledge.blueprints import BLUEPRINTS
        bakery = BLUEPRINTS["bakery"]
        assert "point_of_sale" in bakery["modules"]
        assert "stock" in bakery["modules"]
        assert len(bakery["models"]) > 0
        assert "automations" in bakery
        assert "settings" in bakery
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_knowledge_base.py::TestBlueprintsKnowledge -v`
Expected: FAIL

**Step 3: Create blueprints/__init__.py**

```python
# src/odooforge/knowledge/blueprints/__init__.py
"""Industry blueprint registry — aggregates all blueprint definitions."""

from __future__ import annotations

from odooforge.knowledge.blueprints.bakery import BAKERY
from odooforge.knowledge.blueprints.restaurant import RESTAURANT
from odooforge.knowledge.blueprints.ecommerce import ECOMMERCE
from odooforge.knowledge.blueprints.manufacturing import MANUFACTURING
from odooforge.knowledge.blueprints.services import SERVICES
from odooforge.knowledge.blueprints.retail import RETAIL
from odooforge.knowledge.blueprints.healthcare import HEALTHCARE
from odooforge.knowledge.blueprints.education import EDUCATION
from odooforge.knowledge.blueprints.real_estate import REAL_ESTATE

BLUEPRINTS: dict[str, dict] = {
    "bakery": BAKERY,
    "restaurant": RESTAURANT,
    "ecommerce": ECOMMERCE,
    "manufacturing": MANUFACTURING,
    "services": SERVICES,
    "retail": RETAIL,
    "healthcare": HEALTHCARE,
    "education": EDUCATION,
    "real_estate": REAL_ESTATE,
}
```

**Step 4: Create bakery.py (full example blueprint)**

```python
# src/odooforge/knowledge/blueprints/bakery.py
"""Bakery industry blueprint."""

from __future__ import annotations

BAKERY: dict = {
    "name": "Bakery / Pastry Shop",
    "description": "Complete setup for a bakery or pastry shop with in-store POS, inventory, manufacturing (recipes), and optional online ordering.",
    "modules": [
        "point_of_sale",
        "stock",
        "mrp",
        "purchase",
        "account",
        "contacts",
        "hr",
        "hr_attendance",
        "loyalty",
        "product",
    ],
    "optional_modules": [
        {"module": "website_sale", "when": "online ordering / delivery"},
        {"module": "pos_restaurant", "when": "dine-in seating area"},
        {"module": "delivery", "when": "delivery service"},
        {"module": "hr_holidays", "when": "employee time-off tracking"},
    ],
    "models": [
        {
            "action": "extend",
            "model": "res.partner",
            "fields": [
                {"name": "x_loyalty_tier", "type": "selection",
                 "selection": [["bronze", "Bronze"], ["silver", "Silver"], ["gold", "Gold"]],
                 "description": "Customer loyalty tier based on purchase history"},
                {"name": "x_loyalty_points", "type": "integer",
                 "description": "Accumulated loyalty points"},
                {"name": "x_dietary_notes", "type": "text",
                 "description": "Dietary restrictions or preferences"},
            ],
        },
        {
            "action": "extend",
            "model": "product.template",
            "fields": [
                {"name": "x_allergens", "type": "char",
                 "description": "Allergen information (nuts, gluten, dairy, etc.)"},
                {"name": "x_prep_time_minutes", "type": "integer",
                 "description": "Preparation time in minutes"},
                {"name": "x_is_made_to_order", "type": "boolean",
                 "description": "Whether this item is baked fresh per order"},
                {"name": "x_shelf_life_days", "type": "integer",
                 "description": "Shelf life in days for inventory management"},
            ],
        },
    ],
    "automations": [
        {
            "name": "Update Loyalty Tier",
            "trigger": "on_write",
            "model": "res.partner",
            "trigger_fields": ["x_loyalty_points"],
            "description": "Automatically update loyalty tier when points change: 0-99=Bronze, 100-499=Silver, 500+=Gold",
        },
        {
            "name": "Low Stock Alert",
            "trigger": "on_write",
            "model": "stock.quant",
            "description": "Send notification when ingredient stock falls below reorder point",
        },
        {
            "name": "Welcome Email",
            "trigger": "on_create",
            "model": "res.partner",
            "description": "Send welcome email with loyalty program info to new customers",
        },
    ],
    "settings": {
        "multi_company": False,
        "multi_currency": False,
        "pos_config": {
            "is_loyalty_program": True,
        },
    },
    "sample_data": {
        "product_categories": ["Breads", "Pastries", "Cakes", "Beverages", "Ingredients"],
        "pos_payment_methods": ["Cash", "Card"],
    },
    "multi_location_notes": "For multiple locations: create each as a separate company under a parent, with shared product catalog but separate stock and POS sessions.",
}
```

**Step 5: Create stub blueprints for other industries**

Create these files with minimal structure (we'll flesh them out later). Each follows the same pattern:

```python
# src/odooforge/knowledge/blueprints/restaurant.py
"""Restaurant industry blueprint."""
RESTAURANT: dict = {
    "name": "Restaurant / Food Service",
    "description": "Full restaurant setup with POS, table management, kitchen printing, inventory, and reservations.",
    "modules": ["point_of_sale", "pos_restaurant", "stock", "purchase", "account", "contacts", "hr", "hr_attendance"],
    "optional_modules": [{"module": "website", "when": "online presence / reservations"}],
    "models": [],
    "automations": [],
    "settings": {"multi_company": False},
    "sample_data": {"product_categories": ["Starters", "Main Course", "Desserts", "Beverages"]},
}
```

```python
# src/odooforge/knowledge/blueprints/ecommerce.py
"""eCommerce industry blueprint."""
ECOMMERCE: dict = {
    "name": "eCommerce Store",
    "description": "Online store with product catalog, shopping cart, checkout, payment processing, and shipping.",
    "modules": ["website_sale", "website_sale_stock", "payment", "delivery", "stock", "account", "contacts", "crm", "website_sale_wishlist"],
    "optional_modules": [{"module": "loyalty", "when": "loyalty/rewards program"}, {"module": "website_sale_comparison", "when": "product comparison feature"}],
    "models": [],
    "automations": [],
    "settings": {"multi_company": False},
    "sample_data": {},
}
```

```python
# src/odooforge/knowledge/blueprints/manufacturing.py
"""Manufacturing industry blueprint."""
MANUFACTURING: dict = {
    "name": "Manufacturing / Production",
    "description": "Production management with bills of materials, work orders, quality control, and maintenance.",
    "modules": ["mrp", "mrp_workorder", "quality_control", "stock", "purchase", "sale", "account", "maintenance"],
    "optional_modules": [{"module": "hr", "when": "employee management"}, {"module": "project", "when": "project-based manufacturing"}],
    "models": [],
    "automations": [],
    "settings": {"multi_company": False},
    "sample_data": {},
}
```

```python
# src/odooforge/knowledge/blueprints/services.py
"""Professional services industry blueprint."""
SERVICES: dict = {
    "name": "Professional Services / Consulting",
    "description": "Project-based service company with timesheets, billable hours, CRM, and invoicing.",
    "modules": ["project", "hr_timesheet", "sale_timesheet", "sale", "account", "crm", "contacts", "calendar", "mail"],
    "optional_modules": [{"module": "hr_expense", "when": "expense tracking"}, {"module": "hr_holidays", "when": "time-off management"}],
    "models": [],
    "automations": [],
    "settings": {"multi_company": False},
    "sample_data": {},
}
```

```python
# src/odooforge/knowledge/blueprints/retail.py
"""Retail industry blueprint."""
RETAIL: dict = {
    "name": "Retail Store",
    "description": "Brick-and-mortar retail with POS, inventory, purchasing, and loyalty programs.",
    "modules": ["point_of_sale", "stock", "purchase", "account", "contacts", "loyalty", "pos_sale"],
    "optional_modules": [{"module": "website_sale", "when": "online store"}, {"module": "hr", "when": "employee management"}],
    "models": [],
    "automations": [],
    "settings": {"multi_company": False},
    "sample_data": {},
}
```

```python
# src/odooforge/knowledge/blueprints/healthcare.py
"""Healthcare industry blueprint."""
HEALTHCARE: dict = {
    "name": "Healthcare / Clinic",
    "description": "Patient management, appointments, billing, and inventory for medical supplies.",
    "modules": ["calendar", "account", "contacts", "stock", "hr", "project", "mail"],
    "optional_modules": [{"module": "website", "when": "online appointment booking"}],
    "models": [],
    "automations": [],
    "settings": {"multi_company": False},
    "sample_data": {},
}
```

```python
# src/odooforge/knowledge/blueprints/education.py
"""Education industry blueprint."""
EDUCATION: dict = {
    "name": "Education / Training",
    "description": "Student management, courses, scheduling, and billing for educational institutions.",
    "modules": ["calendar", "account", "contacts", "project", "hr", "website", "mail"],
    "optional_modules": [{"module": "website_sale", "when": "online course enrollment"}],
    "models": [],
    "automations": [],
    "settings": {"multi_company": False},
    "sample_data": {},
}
```

```python
# src/odooforge/knowledge/blueprints/real_estate.py
"""Real estate industry blueprint."""
REAL_ESTATE: dict = {
    "name": "Real Estate / Property Management",
    "description": "Property listings, tenant management, lease tracking, and maintenance requests.",
    "modules": ["crm", "account", "contacts", "project", "calendar", "mail", "website"],
    "optional_modules": [{"module": "hr", "when": "employee management"}],
    "models": [],
    "automations": [],
    "settings": {"multi_company": False},
    "sample_data": {},
}
```

**Step 6: Run all knowledge tests**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_knowledge_base.py -v`
Expected: ALL PASS (including TestKnowledgeBase which can now load all sub-modules)

**Step 7: Commit**

```bash
git add src/odooforge/knowledge/ tests/test_knowledge_base.py
git commit -m "feat: add domain knowledge base with modules, dictionary, patterns, blueprints

Add structured Odoo domain knowledge for the Lovable-for-Odoo intelligence layer:
- Module catalog (~35 core modules with business descriptions)
- Business-to-Odoo dictionary (~60 term mappings)
- Data model patterns (~13 customization patterns)
- Best practices (~22 rules across naming, security, views, performance)
- Industry blueprints (9 industries, bakery fully detailed)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 7: Register MCP resources on server.py

**Files:**
- Modify: `src/odooforge/server.py`
- Modify: `tests/test_server.py`

**Step 1: Add failing test for MCP resources**

Add to `tests/test_server.py`:

```python
class TestServerResources:
    def test_resource_count(self):
        from odooforge.server import mcp
        resources = mcp._resource_manager._resources
        # 5 base resources: modules, dictionary, patterns, best-practices, blueprints-list
        # + 9 blueprint resources (one per industry)
        assert len(resources) >= 5

    def test_modules_resource_registered(self):
        from odooforge.server import mcp
        resources = mcp._resource_manager._resources
        assert "odoo://knowledge/modules" in resources

    def test_dictionary_resource_registered(self):
        from odooforge.server import mcp
        resources = mcp._resource_manager._resources
        assert "odoo://knowledge/dictionary" in resources

    def test_blueprint_template_registered(self):
        from odooforge.server import mcp
        # Template resources use {industry} parameter
        templates = mcp._resource_manager._templates
        found = any("blueprint" in str(t) for t in templates)
        assert found, "Blueprint resource template not registered"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_server.py::TestServerResources -v`
Expected: FAIL — no resources registered

**Step 3: Add resource registrations to server.py**

Add after the `mcp = FastMCP(...)` block and before the tool registrations:

```python
# ── MCP Resources (Domain Knowledge) ─────────────────────────────

import json

@mcp.resource("odoo://knowledge/modules",
              name="Odoo Module Catalog",
              description="~35 Odoo 18 modules mapped to business needs with descriptions and dependencies.",
              mime_type="application/json")
def knowledge_modules() -> str:
    from odooforge.knowledge import KnowledgeBase
    kb = KnowledgeBase()
    return json.dumps(kb.get_modules(), indent=2)


@mcp.resource("odoo://knowledge/dictionary",
              name="Business-to-Odoo Dictionary",
              description="Maps ~60 business terms (customer, invoice, warehouse) to Odoo models with filters and tips.",
              mime_type="application/json")
def knowledge_dictionary() -> str:
    from odooforge.knowledge import KnowledgeBase
    kb = KnowledgeBase()
    return json.dumps(kb.get_dictionary(), indent=2)


@mcp.resource("odoo://knowledge/patterns",
              name="Data Model Patterns",
              description="~13 common Odoo customization patterns with ingredients and approach (configuration vs code generation).",
              mime_type="application/json")
def knowledge_patterns() -> str:
    from odooforge.knowledge import KnowledgeBase
    kb = KnowledgeBase()
    return json.dumps(kb.get_patterns(), indent=2)


@mcp.resource("odoo://knowledge/best-practices",
              name="Odoo Best Practices",
              description="~22 Odoo conventions and guidelines for naming, security, views, performance, and automation.",
              mime_type="application/json")
def knowledge_best_practices() -> str:
    from odooforge.knowledge import KnowledgeBase
    kb = KnowledgeBase()
    return json.dumps(kb.get_best_practices(), indent=2)


@mcp.resource("odoo://knowledge/blueprints",
              name="Industry Blueprints Index",
              description="List of available industry blueprints with names and descriptions.",
              mime_type="application/json")
def knowledge_blueprints_index() -> str:
    from odooforge.knowledge import KnowledgeBase
    kb = KnowledgeBase()
    index = {}
    for bp_id in kb.list_blueprints():
        bp = kb.get_blueprint(bp_id)
        if bp:
            index[bp_id] = {"name": bp["name"], "description": bp["description"]}
    return json.dumps(index, indent=2)


@mcp.resource("odoo://knowledge/blueprints/{industry}",
              name="Industry Blueprint",
              description="Detailed industry blueprint with modules, models, automations, and settings.",
              mime_type="application/json")
def knowledge_blueprint(industry: str) -> str:
    from odooforge.knowledge import KnowledgeBase
    kb = KnowledgeBase()
    bp = kb.get_blueprint(industry)
    if bp is None:
        available = kb.list_blueprints()
        return json.dumps({"error": f"Unknown industry: {industry}", "available": available})
    return json.dumps(bp, indent=2)
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/test_server.py::TestServerResources -v`
Expected: PASS

Note: The test for resource templates may need adjustment based on the actual FastMCP internal API. Check `mcp._resource_manager` attributes if the test fails and adjust accordingly.

**Step 5: Run ALL existing tests to verify nothing broke**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/ -v`
Expected: ALL PASS (existing 71-tool tests + new resource tests)

**Step 6: Commit**

```bash
git add src/odooforge/server.py tests/test_server.py
git commit -m "feat: register domain knowledge as MCP resources

Expose KnowledgeBase through 6 MCP resources:
- odoo://knowledge/modules (module catalog)
- odoo://knowledge/dictionary (business-to-Odoo mappings)
- odoo://knowledge/patterns (customization patterns)
- odoo://knowledge/best-practices (conventions)
- odoo://knowledge/blueprints (index)
- odoo://knowledge/blueprints/{industry} (per-industry details)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 8: Update hatch build config to include knowledge files

**Files:**
- Modify: `pyproject.toml`

**Step 1: Verify knowledge files would be included in package**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -c "from odooforge.knowledge import KnowledgeBase; kb = KnowledgeBase(); print(f'Modules: {len(kb.get_modules())}, Dict: {len(kb.get_dictionary())}, Patterns: {len(kb.get_patterns())}, Blueprints: {len(kb.list_blueprints())}')"`
Expected: Shows counts for all knowledge categories

Since knowledge is pure Python (`.py` files, not YAML/JSON data files), it's automatically included in the wheel by hatch. No `pyproject.toml` changes needed.

**Step 2: Run full test suite one final time**

Run: `cd /Users/zeus/Desktop/projects/odooforge && python -m pytest tests/ -v`
Expected: ALL PASS

**Step 3: Commit (if pyproject.toml needed changes, otherwise skip)**

---

### Task 9: Manual smoke test with MCP

**Step 1: Test the MCP server starts**

Run: `cd /Users/zeus/Desktop/projects/odooforge && timeout 5 python -m odooforge 2>&1 || true`
Expected: Server starts without import errors (may timeout or fail on connection — that's fine, we're testing imports)

**Step 2: Verify resources are accessible via MCP inspector (optional)**

If mcp CLI is available:
Run: `cd /Users/zeus/Desktop/projects/odooforge && npx @modelcontextprotocol/inspector python -m odooforge`

Check that all 6 resources appear in the inspector's resource list.

---

## Phase 2-6 Outlines (future plans)

### Phase 2: MCP Prompts (Layer 4a)
- Register 4 MCP prompts on server.py: `business-setup`, `feature-builder`, `module-generator`, `troubleshooter`
- Each prompt is a string template returned by `@mcp.prompt()` decorated functions
- Test: prompts registered and return non-empty strings

### Phase 3: Planning Tools (Layer 3)
- Create `src/odooforge/planning/` package
- `requirement_parser.py` — keyword matching against knowledge base
- `solution_designer.py` — template-based plan generation from blueprints
- `plan_validator.py` — check plan against live instance state
- Register 3 new tools: `odoo_analyze_requirements`, `odoo_design_solution`, `odoo_validate_plan`
- Update tool count test to 74

### Phase 4: Workflow Tools (Layer 2)
- Create `src/odooforge/workflows/` package
- `executor.py` — step-by-step plan execution with rollback
- `rollback.py` — snapshot-based recovery
- Register workflow tools: `odoo_setup_business`, `odoo_create_feature`, `odoo_create_dashboard`, `odoo_setup_integration`
- Update tool count test to 78

### Phase 5: Code Generation (Layer 2)
- Create `src/odooforge/codegen/` package
- Jinja2 templates (or string.Template) for manifest, models, views, security
- `scaffold.py` — directory structure generation
- `deployer.py` — hot-reload or git scaffold
- Register `odoo_generate_addon` tool
- Update tool count test to 79

### Phase 6: Claude Code Skills (parallel)
- Create `skills/odoo-brainstorm.md`, `skills/odoo-architect.md`, `skills/odoo-debug.md`
- Distribution: include in repo, document installation in README
