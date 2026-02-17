---
name: odoo-brainstorm
description: Use when exploring Odoo customization ideas — discovers modules, matches blueprints, decides configuration vs code generation
---

# Odoo Brainstorm

Explore Odoo customization ideas with domain-specific knowledge.

## When to Use

- User wants to add business functionality to Odoo
- User describes a business need but doesn't know Odoo's capabilities
- Planning a new Odoo deployment or major feature addition

## Process

### 1. Understand the Business Context

Ask about:
- Industry / business type
- Number of users, locations, companies
- Existing systems being replaced
- Key pain points

### 2. Discover Relevant Modules

Use OdooForge tools to explore:

```
odoo_analyze_requirements("user's business description")
```

This returns:
- Matching industry blueprint
- Needed modules with reasons
- Custom requirements (config vs code)
- Infrastructure needs
- Clarifying questions

Also check the knowledge resources:
- `odoo://knowledge/modules` — 35 Odoo 18 modules mapped to business language
- `odoo://knowledge/blueprints` — 9 industry blueprints
- `odoo://knowledge/dictionary` — business term to Odoo model mapping

### 3. Configuration vs Code Decision

For each requirement, determine the approach:

| Approach | When | Tools |
|----------|------|-------|
| **Configuration** | Standard fields, views, automations | `odoo_schema_field_create`, `odoo_view_modify`, `odoo_automation_create` |
| **Workflow** | Complete features or business setup | `odoo_create_feature`, `odoo_setup_business` |
| **Code Generation** | Custom models, complex logic, new apps | `odoo_generate_addon` |

Decision criteria:
- Can it be done with `x_` custom fields? Use configuration
- Does it need new models with business logic? Use code generation
- Is it a standard industry setup? Use a blueprint via `odoo_setup_business`

### 4. Check Existing State

Before proposing changes, check what's already there:
- `odoo_module_list_installed` — what's already installed
- `odoo_model_list` — existing data models
- `odoo_model_fields` — fields on target models
- `odoo_schema_list_custom` — existing customizations

### 5. Present Options

Present 2-3 approaches with trade-offs:
- **Quick win**: Configuration-only approach (fastest, least risk)
- **Full feature**: Workflow tool approach (complete, snapshot-backed)
- **Custom app**: Code generation approach (most flexible, requires deployment)

Always recommend starting with `odoo_analyze_requirements` to get a structured analysis.

## Key Principles

- **Start with what exists** — check installed modules and existing customizations first
- **Prefer configuration over code** — `x_` fields and automations are simpler to maintain
- **Use blueprints when they fit** — 9 industry blueprints cover common setups
- **Snapshot before changes** — every modification should start with a snapshot
- **Ask about data** — existing data migration needs often drive architecture decisions
