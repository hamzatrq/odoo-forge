"""Odoo 18 module catalog — business-friendly metadata for core modules."""

from __future__ import annotations

from typing import Any

# ── Module Knowledge Catalog ──────────────────────────────────────
#
# Each entry maps a technical module name to structured metadata that
# helps an AI assistant understand *what the module does in business
# terms*, which modules it depends on, and what kinds of business
# needs it addresses.

MODULES: dict[str, dict[str, Any]] = {
    # ── Sales ─────────────────────────────────────────────────────
    "sale": {
        "name": "Sales",
        "business_description": (
            "Manage the full sales cycle from quotations to confirmed sales "
            "orders. Track order status, apply pricelists and discounts, "
            "and generate invoices automatically when orders are delivered "
            "or confirmed."
        ),
        "category": "sales",
        "depends": ["contacts", "account"],
        "business_needs": [
            "selling products or services",
            "creating quotations",
            "managing sales orders",
            "applying pricelists and discounts",
            "tracking order fulfillment",
        ],
    },
    "crm": {
        "name": "CRM",
        "business_description": (
            "Track leads and opportunities through a visual pipeline. "
            "Assign salespeople, schedule activities, forecast revenue, "
            "and analyze win/loss ratios to improve sales performance."
        ),
        "category": "sales",
        "depends": ["contacts", "mail"],
        "business_needs": [
            "lead management",
            "sales pipeline tracking",
            "opportunity forecasting",
            "sales team performance",
            "customer follow-up activities",
        ],
    },
    "sale_crm": {
        "name": "Sales + CRM Integration",
        "business_description": (
            "Bridges CRM and Sales so that won opportunities automatically "
            "create quotations. Tracks the full journey from lead to "
            "revenue in a single workflow."
        ),
        "category": "sales",
        "depends": ["sale", "crm"],
        "business_needs": [
            "converting leads to quotations",
            "end-to-end sales tracking",
            "revenue attribution to pipeline",
        ],
    },

    # ── Purchasing ────────────────────────────────────────────────
    "purchase": {
        "name": "Purchase",
        "business_description": (
            "Create and manage purchase orders and requests for quotation "
            "(RFQ). Track vendor prices, automate reordering, and "
            "streamline the procurement-to-payment cycle."
        ),
        "category": "purchasing",
        "depends": ["contacts", "account"],
        "business_needs": [
            "purchasing products",
            "managing vendors and supplier prices",
            "requests for quotation",
            "procurement automation",
            "purchase approval workflows",
        ],
    },

    # ── Accounting & Finance ──────────────────────────────────────
    "account": {
        "name": "Invoicing / Accounting",
        "business_description": (
            "Full double-entry accounting with invoicing, vendor bills, "
            "bank reconciliation, tax management, and financial reports. "
            "Supports multi-currency and multi-company setups."
        ),
        "category": "accounting",
        "depends": ["contacts"],
        "business_needs": [
            "invoicing customers",
            "recording vendor bills",
            "bank reconciliation",
            "tax computation and reporting",
            "financial statements",
            "multi-currency transactions",
        ],
    },
    "account_payment": {
        "name": "Payment Follow-up",
        "business_description": (
            "Automate payment reminders and follow-up actions for overdue "
            "invoices. Define escalation levels and send reminders by email "
            "or letter."
        ),
        "category": "accounting",
        "depends": ["account"],
        "business_needs": [
            "payment follow-up",
            "overdue invoice reminders",
            "collections management",
            "aging reports",
        ],
    },

    # ── Inventory & Warehousing ───────────────────────────────────
    "stock": {
        "name": "Inventory",
        "business_description": (
            "Warehouse and inventory management with real-time stock levels, "
            "barcode scanning, lot/serial tracking, and multi-step routes "
            "for receipts, deliveries, and internal transfers."
        ),
        "category": "inventory",
        "depends": ["product"],
        "business_needs": [
            "tracking stock levels",
            "warehouse management",
            "barcode scanning",
            "lot and serial number tracking",
            "multi-warehouse operations",
            "inventory adjustments",
        ],
    },
    "stock_account": {
        "name": "Inventory Valuation",
        "business_description": (
            "Bridges inventory and accounting so that stock moves "
            "automatically generate journal entries. Supports FIFO, "
            "average cost, and standard price valuation methods."
        ),
        "category": "inventory",
        "depends": ["stock", "account"],
        "business_needs": [
            "inventory valuation",
            "cost of goods sold tracking",
            "automated stock accounting",
        ],
    },
    "delivery": {
        "name": "Delivery / Shipping",
        "business_description": (
            "Configure shipping methods and carriers, compute shipping "
            "rates, print shipping labels, and track packages. Integrates "
            "with major carriers like UPS, FedEx, DHL."
        ),
        "category": "inventory",
        "depends": ["stock"],
        "business_needs": [
            "shipping management",
            "carrier rate computation",
            "shipping label printing",
            "package tracking",
        ],
    },

    # ── Manufacturing ─────────────────────────────────────────────
    "mrp": {
        "name": "Manufacturing (MRP)",
        "business_description": (
            "Plan and execute production with Bills of Materials, "
            "manufacturing orders, and material requirements planning. "
            "Track raw material consumption and finished goods output."
        ),
        "category": "manufacturing",
        "depends": ["stock"],
        "business_needs": [
            "production planning",
            "bills of materials",
            "manufacturing orders",
            "raw material management",
            "production scheduling",
        ],
    },
    "mrp_workorder": {
        "name": "Work Orders",
        "business_description": (
            "Break manufacturing orders into step-by-step work orders "
            "assigned to specific work centers. Track time, quality checks, "
            "and production steps on the shop floor."
        ),
        "category": "manufacturing",
        "depends": ["mrp"],
        "business_needs": [
            "shop floor management",
            "work center scheduling",
            "production step tracking",
            "work order instructions",
        ],
    },
    "quality_control": {
        "name": "Quality Control",
        "business_description": (
            "Define quality check points in manufacturing and inventory "
            "operations. Create quality alerts, track pass/fail rates, "
            "and enforce quality standards."
        ),
        "category": "manufacturing",
        "depends": ["stock"],
        "business_needs": [
            "quality inspections",
            "quality control checks",
            "quality alerts and tracking",
            "compliance management",
        ],
    },
    "maintenance": {
        "name": "Maintenance",
        "business_description": (
            "Schedule and track preventive and corrective maintenance "
            "for equipment and machines. Log maintenance requests, "
            "track equipment history, and minimize downtime."
        ),
        "category": "manufacturing",
        "depends": ["mail"],
        "business_needs": [
            "equipment maintenance scheduling",
            "preventive maintenance",
            "maintenance requests",
            "equipment tracking",
        ],
    },

    # ── Point of Sale ─────────────────────────────────────────────
    "point_of_sale": {
        "name": "Point of Sale",
        "business_description": (
            "Browser-based POS terminal for retail and restaurant. "
            "Works online and offline, supports barcode scanning, "
            "multiple payment methods, and receipt printing."
        ),
        "category": "pos",
        "depends": ["stock", "account"],
        "business_needs": [
            "retail checkout",
            "POS terminal",
            "cash register",
            "barcode scanning at checkout",
            "receipt printing",
        ],
    },
    "pos_restaurant": {
        "name": "POS Restaurant",
        "business_description": (
            "Extends Point of Sale with restaurant-specific features: "
            "floor plans, table management, order splitting, kitchen "
            "printing, and tip handling."
        ),
        "category": "pos",
        "depends": ["point_of_sale"],
        "business_needs": [
            "restaurant order management",
            "table management",
            "kitchen printing",
            "order splitting",
            "floor plan layout",
        ],
    },
    "pos_sale": {
        "name": "POS + Sales Integration",
        "business_description": (
            "Allows sales orders to be loaded and paid at the POS. "
            "Useful for pick-up orders, layaway, or bridging online "
            "and in-store sales."
        ),
        "category": "pos",
        "depends": ["point_of_sale", "sale"],
        "business_needs": [
            "paying sales orders at POS",
            "pick-up orders",
            "bridging online and in-store",
        ],
    },
    "loyalty": {
        "name": "Loyalty & Promotions",
        "business_description": (
            "Create loyalty programs, discount coupons, promotional "
            "campaigns, and gift card programs. Works with both POS "
            "and eCommerce."
        ),
        "category": "pos",
        "depends": [],
        "business_needs": [
            "loyalty programs",
            "discount coupons",
            "promotional campaigns",
            "gift cards",
            "customer rewards",
        ],
    },

    # ── Website & eCommerce ───────────────────────────────────────
    "website": {
        "name": "Website Builder",
        "business_description": (
            "Drag-and-drop website builder with pages, menus, themes, "
            "and SEO tools. Create a professional web presence without "
            "coding."
        ),
        "category": "website",
        "depends": [],
        "business_needs": [
            "company website",
            "landing pages",
            "blog",
            "web presence",
            "SEO optimization",
        ],
    },
    "website_sale": {
        "name": "eCommerce",
        "business_description": (
            "Full-featured online store with product catalog, shopping "
            "cart, checkout, and payment processing. Syncs with inventory "
            "and accounting automatically."
        ),
        "category": "website",
        "depends": ["website", "sale"],
        "business_needs": [
            "online store",
            "selling products online",
            "shopping cart and checkout",
            "online payments",
        ],
    },
    "website_sale_stock": {
        "name": "eCommerce + Inventory",
        "business_description": (
            "Shows real-time stock availability on the website. Customers "
            "see whether products are in stock, and sold-out products can "
            "be hidden or marked automatically."
        ),
        "category": "website",
        "depends": ["website_sale", "stock"],
        "business_needs": [
            "showing stock availability online",
            "hiding out-of-stock products",
            "real-time inventory on website",
        ],
    },
    "website_sale_wishlist": {
        "name": "eCommerce Wishlist",
        "business_description": (
            "Lets customers save products to a wishlist for later "
            "purchase. Useful for improving conversion and understanding "
            "customer preferences."
        ),
        "category": "website",
        "depends": ["website_sale"],
        "business_needs": [
            "customer wishlists",
            "save-for-later functionality",
        ],
    },
    "website_sale_comparison": {
        "name": "Product Comparison",
        "business_description": (
            "Allows website visitors to compare products side-by-side "
            "based on attributes. Helpful for stores with technical or "
            "configurable products."
        ),
        "category": "website",
        "depends": ["website_sale"],
        "business_needs": [
            "product comparison",
            "side-by-side feature comparison",
        ],
    },
    "payment": {
        "name": "Payment Providers",
        "business_description": (
            "Framework for integrating payment providers (Stripe, PayPal, "
            "Adyen, etc.) into invoicing, eCommerce, and subscriptions. "
            "Handles tokenization and payment flows."
        ),
        "category": "website",
        "depends": ["account"],
        "business_needs": [
            "online payment processing",
            "payment gateway integration",
            "credit card payments",
        ],
    },

    # ── Human Resources ───────────────────────────────────────────
    "hr": {
        "name": "Employees",
        "business_description": (
            "Core HR module for employee records, departments, job "
            "positions, and organizational charts. Foundation for all "
            "other HR modules."
        ),
        "category": "hr",
        "depends": [],
        "business_needs": [
            "employee records",
            "department management",
            "organizational chart",
            "job positions",
        ],
    },
    "hr_holidays": {
        "name": "Time Off",
        "business_description": (
            "Manage employee leave requests, approval workflows, leave "
            "types (vacation, sick, etc.), and accrual policies. "
            "Integrates with the company calendar."
        ),
        "category": "hr",
        "depends": ["hr"],
        "business_needs": [
            "leave management",
            "vacation tracking",
            "time off approvals",
            "leave accrual policies",
        ],
    },
    "hr_attendance": {
        "name": "Attendance",
        "business_description": (
            "Track employee check-in and check-out times. Supports "
            "kiosk mode for on-site attendance, PIN-based identification, "
            "and overtime calculations."
        ),
        "category": "hr",
        "depends": ["hr"],
        "business_needs": [
            "attendance tracking",
            "check-in/check-out",
            "overtime management",
            "kiosk attendance",
        ],
    },
    "hr_expense": {
        "name": "Expenses",
        "business_description": (
            "Submit, approve, and reimburse employee expense reports. "
            "Supports receipt scanning, mileage tracking, and automatic "
            "journal entries for accounting."
        ),
        "category": "hr",
        "depends": ["hr", "account"],
        "business_needs": [
            "expense reports",
            "expense reimbursement",
            "receipt management",
            "travel expense tracking",
        ],
    },
    "hr_recruitment": {
        "name": "Recruitment",
        "business_description": (
            "Manage job postings, applicant tracking, interview scheduling, "
            "and hiring pipeline. Track candidates from application to "
            "employee onboarding."
        ),
        "category": "hr",
        "depends": ["hr"],
        "business_needs": [
            "job postings",
            "applicant tracking",
            "interview management",
            "hiring pipeline",
        ],
    },
    "hr_timesheet": {
        "name": "Timesheets",
        "business_description": (
            "Record employee time spent on projects and tasks. Generate "
            "timesheet reports and link hours to project billing and "
            "cost tracking."
        ),
        "category": "hr",
        "depends": ["hr", "project"],
        "business_needs": [
            "time tracking",
            "timesheet entry",
            "project time recording",
            "billable hours tracking",
        ],
    },

    # ── Project Management ────────────────────────────────────────
    "project": {
        "name": "Project",
        "business_description": (
            "Organize work into projects and tasks with Kanban boards, "
            "deadlines, priorities, and team assignments. Track progress "
            "and manage workloads visually."
        ),
        "category": "project",
        "depends": ["mail"],
        "business_needs": [
            "project management",
            "task tracking",
            "team workload management",
            "Kanban boards",
            "deadline tracking",
        ],
    },
    "sale_timesheet": {
        "name": "Sales + Timesheets",
        "business_description": (
            "Bill customers based on timesheet hours recorded against "
            "sales orders. Supports fixed-price and time-and-materials "
            "billing for service companies."
        ),
        "category": "project",
        "depends": ["sale", "hr_timesheet"],
        "business_needs": [
            "billing based on timesheets",
            "time-and-materials invoicing",
            "service project billing",
        ],
    },

    # ── Communication ─────────────────────────────────────────────
    "mail": {
        "name": "Discuss",
        "business_description": (
            "Internal messaging, activity scheduling, and email "
            "integration. Powers the chatter (message thread) on every "
            "record and notification system across Odoo."
        ),
        "category": "communication",
        "depends": [],
        "business_needs": [
            "internal messaging",
            "email integration",
            "activity scheduling",
            "record discussions",
            "notifications",
        ],
    },
    "calendar": {
        "name": "Calendar",
        "business_description": (
            "Shared calendar for scheduling meetings, appointments, and "
            "events. Syncs with Google Calendar and Outlook. Supports "
            "reminders and attendee management."
        ),
        "category": "communication",
        "depends": ["mail"],
        "business_needs": [
            "meeting scheduling",
            "shared calendars",
            "appointment booking",
            "calendar sync",
        ],
    },

    # ── Contacts & Products ───────────────────────────────────────
    "contacts": {
        "name": "Contacts",
        "business_description": (
            "Centralized address book for customers, vendors, and contacts. "
            "Supports companies and individuals, with addresses, tags, and "
            "communication history."
        ),
        "category": "core",
        "depends": ["mail"],
        "business_needs": [
            "customer management",
            "vendor management",
            "contact directory",
            "address book",
        ],
    },
    "product": {
        "name": "Products",
        "business_description": (
            "Product catalog with variants, categories, units of measure, "
            "and pricing. Foundation for sales, purchasing, inventory, "
            "and manufacturing modules."
        ),
        "category": "core",
        "depends": [],
        "business_needs": [
            "product catalog",
            "product variants",
            "product categories",
            "unit of measure management",
            "pricing management",
        ],
    },
}
