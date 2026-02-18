---
name: odoo-report
description: Use when building dashboards, analyzing business data, or creating reports — KPI definition, SQL analytics, dashboard creation
---

# Odoo Reports & Analytics

Guide dashboard creation, data analysis, and business reporting.

## When to Use

- User asks "how are sales?" or similar analysis questions
- User wants to build a dashboard or report
- User wants KPIs or metrics tracked
- User asks about business performance

## Process

### 1. Understand What to Measure

Ask about:
- What business question are you trying to answer?
- What time period? (this week, month, quarter, year)
- Compare to what? (previous period, target, other segments)
- Who will see this? (management, team, specific role)

### 2. Analyze Data

**Delegate to the odoo-analyst agent** for complex queries:
- The analyst uses SQL for aggregations and joins
- The analyst translates Odoo data into business insights
- The analyst recommends dashboards based on the data

For quick answers, query directly:
```
odoo_db_run_sql(db_name="db", query="SELECT ... FROM sale_order WHERE ...")
odoo_record_search(db_name="db", model="sale.order", domain=[...], count_only=True)
```

### 3. Build Dashboards

For persistent dashboards in Odoo:
```
odoo_create_dashboard(
    db_name="db",
    name="Sales Dashboard",
    metrics=[
        {"model": "sale.order", "measure": "amount_total", "group_by": "date_order:month"},
        {"model": "sale.order", "measure": "__count", "domain": [["state", "=", "sale"]]}
    ]
)
```

### 4. Create Custom Reports

For QWeb reports:
```
odoo_report_list(db_name="db", model="sale.order")
odoo_report_modify(db_name="db", report_name="...", xpath="...", content="...")
```

## Common Business Metrics

| Metric | Model | Measure | Filter |
|--------|-------|---------|--------|
| Total Revenue | `sale.order` | `amount_total` | `state = 'sale'` |
| Open Orders | `sale.order` | `__count` | `state = 'draft'` |
| New Customers | `res.partner` | `__count` | `create_date >= this_month` |
| Products Sold | `sale.order.line` | `product_uom_qty` | via sale order |
| Outstanding Invoices | `account.move` | `amount_residual` | `state = 'posted', payment_state != 'paid'` |
| Stock Value | `stock.valuation.layer` | `value` | current |
| Employee Count | `hr.employee` | `__count` | `active = True` |

## Key Principles

- **Business language** — say "revenue" not "amount_total", "customers" not "res.partner"
- **Context matters** — always include time period, comparison, and what "good" looks like
- **Actionable insights** — don't just show numbers, suggest what to do about them
- **Read-only** — analysis should never modify data
