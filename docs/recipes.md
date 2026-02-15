# Industry Recipes

Recipes are pre-built configurations that set up an Odoo instance for a specific industry. Each recipe installs the right modules, creates initial data, and provides post-setup guidance.

## Available Recipes

### 🍕 Restaurant / Food Service

**ID:** `restaurant`

Full restaurant setup with point-of-sale, inventory tracking, and kitchen management.

**Modules installed:**
- `point_of_sale` — POS terminal
- `pos_restaurant` — Table management and floor plans
- `stock` — Inventory tracking
- `purchase` — Supplier ordering
- `account` — Accounting
- `contacts` — Customer/supplier management
- `hr` — Employee management
- `hr_attendance` — Attendance tracking

**Auto-configured:**
- Table management enabled
- Kitchen order printing enabled
- Product categories: Food, Beverages, Desserts

**Post-setup:** Configure menu items, set up printers for kitchen/bar, and create employee PINs.

---

### 🛒 eCommerce Store

**ID:** `ecommerce`

Online store with website, product catalog, payments, and shipping.

**Modules installed:**
- `website_sale` — Online shop
- `website_sale_stock` — Stock visibility on website
- `payment` — Payment processing
- `delivery` — Shipping methods
- `stock` — Inventory
- `account` — Accounting
- `contacts` — Customer management
- `crm` — Lead tracking
- `website_sale_wishlist` — Customer wishlists
- `website_sale_comparison` — Product comparison

**Auto-configured:**
- Buy button enabled on product pages

**Post-setup:** Add products with images, configure shipping methods, and set up payment providers (Stripe/PayPal).

---

### 🏭 Manufacturing / Production

**ID:** `manufacturing`

Production management with bills of materials, work orders, and quality control.

**Modules installed:**
- `mrp` — Manufacturing Resource Planning
- `mrp_workorder` — Work order management
- `quality_control` — Quality checks
- `stock` — Inventory and warehousing
- `purchase` — Raw material purchasing
- `sale` — Sales orders
- `account` — Accounting
- `maintenance` — Equipment maintenance

**Auto-configured:**
- Work centers: Assembly Line, Quality Check

**Post-setup:** Create Bills of Materials, define routings, and set reorder rules for raw materials.

---

### 💼 Professional Services / Consulting

**ID:** `services`

Project-based service company with timesheets, billing, and CRM pipeline.

**Modules installed:**
- `project` — Project management
- `timesheet_grid` — Timesheet grid view
- `sale_timesheet` — Billable timesheets
- `hr_timesheet` — Employee timesheets
- `account` — Invoicing
- `crm` — Sales pipeline
- `sale` — Quotations and orders
- `contacts` — Client management
- `calendar` — Scheduling
- `mail` — Communication

**Auto-configured:**
- Project stages: Backlog → In Progress → Review → Done

**Post-setup:** Create service products, set hourly rates, and configure invoice policies.

---

### 🏪 Retail Store

**ID:** `retail`

Brick-and-mortar retail with POS, inventory management, and loyalty programs.

**Modules installed:**
- `point_of_sale` — POS terminal
- `stock` — Inventory tracking
- `purchase` — Supplier purchasing
- `account` — Accounting
- `contacts` — Customer database
- `loyalty` — Loyalty programs
- `pos_sale` — POS-to-sale order integration

**Auto-configured:**
- Loyalty program support enabled

**Post-setup:** Import product catalog, set up barcode labels, and configure loyalty programs.

## Usage

### List recipes

```
"Show me all available recipes"
```

### Preview a recipe (dry run)

```
"Run the ecommerce recipe in dry-run mode"
```

This shows exactly what modules will be installed and what steps will be performed, without making any changes.

### Execute a recipe

```
"Execute the restaurant recipe"
```

> **Tip:** Always create a snapshot before executing a recipe: `"Create a snapshot called pre-recipe"`
