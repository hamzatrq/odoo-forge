---
name: odoo-architect
description: Use when designing Odoo data models — enforces naming conventions, inheritance patterns, security, and field best practices
---

# Odoo Data Model Architect

Guide Odoo data model design with best practices and conventions.

## When to Use

- Designing new custom models for Odoo
- Adding fields to existing models
- Planning model inheritance and relationships
- Setting up security groups and access rules

## Design Checklist

For every new model, verify these decisions:

### 1. Model Type

| Type | Use When | Example |
|------|----------|---------|
| `models.Model` | Persistent data | Customer records, orders |
| `models.TransientModel` | Temporary/wizard data | Import wizards, config dialogs |
| `models.AbstractModel` | Shared behavior (mixin) | Common fields across models |

### 2. Naming Conventions

Follow the knowledge base best practices (`odoo://knowledge/best-practices`):

- **Model name**: `x_module.entity` (e.g., `x_recipe.ingredient`)
- **Field names**: `x_` prefix for custom fields (e.g., `x_loyalty_tier`)
- **Field labels**: Human-readable, title case (e.g., "Loyalty Tier")
- **Relations**: `x_entity_id` for Many2one, `x_entity_ids` for Many2many
- **Module name**: lowercase with underscores (e.g., `x_recipe_manager`)

### 3. Mandatory Mixins Checklist

| Mixin | Include When | What It Adds |
|-------|-------------|--------------|
| `mail.thread` | Model needs communication history | Chatter, followers, email tracking |
| `mail.activity.mixin` | Model needs scheduled activities | Activity scheduling, reminders |
| `portal.mixin` | Records visible to portal users | Portal access, sharing |

### 4. Common Patterns

Check `odoo://knowledge/patterns` for these patterns:

- **Trackable model**: `mail.thread` + stages + kanban
- **Partner extension**: Custom fields on `res.partner`
- **Product extension**: Custom fields on `product.template`
- **Approval workflow**: Stages with validation rules
- **Scheduled job**: `ir.cron` for recurring tasks

### 5. Field Design Rules

```
Type Selection Guide:
  Text data
    Short (< 256 chars)        -> Char
    Long (multi-line)          -> Text
    Rich text                  -> Html
  Numbers
    Whole numbers              -> Integer
    Decimals                   -> Float
    Money                      -> Monetary (requires currency_id)
  Dates
    Date only                  -> Date
    Date + time                -> Datetime
  Choices
    Fixed options              -> Selection
    Dynamic options            -> Many2one
  Relations
    Many records, one parent   -> Many2one
    One parent, many children  -> One2many
    Many to many               -> Many2many
  Other
    Yes/no                     -> Boolean
    Files/images               -> Binary
```

### 6. Security Design

Every model needs:
1. **Access rules** (`ir.model.access.csv`): Who can CRUD
2. **Record rules** (`ir.rule`): Which records they can see
3. **Groups**: Role-based access (user vs manager)

Use `odoo_generate_addon` with `security_groups` parameter to auto-generate security scaffolding.

### 7. Multi-Company Support

If the deployment has multiple companies:
- Add `company_id = fields.Many2one('res.company')` to every model
- Add record rules filtering by company
- Use `odoo_setup_business` with `locations > 1` to set up multi-company

## Output

After the design session, produce:
1. **Model spec** ready for `odoo_generate_addon` (JSON format)
2. **Field list** ready for `odoo_create_feature` or `odoo_schema_field_create`
3. **Security groups** if custom roles needed
4. **Blueprint reference** if an industry blueprint applies
