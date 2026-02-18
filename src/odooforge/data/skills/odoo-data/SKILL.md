---
name: odoo-data
description: Use when importing, creating, or managing business data in Odoo — CSV imports, bulk record creation, data migration, user setup
---

# Odoo Data Manager

Guide data import and record management workflows.

## When to Use

- User wants to import data (CSV, spreadsheet)
- User wants to create records in bulk
- User wants to migrate data from another system
- User wants to set up users, products, contacts, or other master data

## Process

### 1. Understand the Data

Ask about:
- What data are you importing? (contacts, products, invoices, etc.)
- What format is it in? (CSV, Excel, manual entry)
- How many records?
- Is this a one-time import or recurring?

### 2. Prepare

Check the target model's fields:
```
odoo_model_fields(db_name="db", model="target.model")
```

For CSV imports, generate a template:
```
odoo_csv_template(db_name="db", model="target.model")
```

Preview the import before executing:
```
odoo_csv_preview(db_name="db", model="target.model", csv_path="path/to/file.csv")
```

### 3. Import / Create

For CSV:
```
odoo_csv_import(db_name="db", model="target.model", csv_path="path/to/file.csv")
```

For individual records:
```
odoo_record_create(db_name="db", model="target.model", values={...})
```

For bulk creation, use a loop with `odoo_record_create` or prepare a CSV.

### 4. Verify

After import:
- Count records: `odoo_record_search` with domain filters
- Spot-check a few records: `odoo_record_read`
- Check for errors in logs: `odoo_instance_logs`

## Data Migration Checklist

When migrating from another system:

1. **Map fields** — match source columns to Odoo fields using `odoo://knowledge/dictionary`
2. **Handle relations** — import parent records first (companies before contacts, categories before products)
3. **Clean data** — remove duplicates, fix formats before import
4. **Test small** — import 10 records first, verify, then do the full batch
5. **Snapshot** — always create a snapshot before large imports

## Common Data Types

| Data | Odoo Model | Key Fields |
|------|-----------|------------|
| Contacts | `res.partner` | `name`, `email`, `phone`, `type` |
| Products | `product.template` | `name`, `list_price`, `type`, `categ_id` |
| Sales Orders | `sale.order` | `partner_id`, `order_line` |
| Invoices | `account.move` | `partner_id`, `move_type`, `invoice_line_ids` |
| Employees | `hr.employee` | `name`, `department_id`, `job_id` |

## Key Principles

- **Preview before import** — always use `odoo_csv_preview` first
- **Snapshot before bulk operations** — create a restore point
- **Import order matters** — parent records before children
- **Verify after import** — count records and spot-check
