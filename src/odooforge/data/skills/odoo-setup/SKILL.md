---
name: odoo-setup
description: Use when setting up Odoo for a business — guides the full Discover, Plan, Build flow from natural language requirements
---

# Odoo Business Setup

Guide the complete business deployment workflow from natural language description to configured Odoo instance.

## When to Use

- User describes their business and wants Odoo configured
- User wants to set up a new Odoo instance for a specific industry
- User says "set up", "configure", "deploy", or "get started with Odoo"

## Process

### 1. Discover — Understand the Business

Ask about:
- What does the business do? (industry, products/services)
- How many people, locations, companies?
- What are the key workflows? (sales, inventory, manufacturing, etc.)
- Any existing systems or data to migrate?

Then run analysis:
```
odoo_analyze_requirements("<user's business description>")
```

Review the output with the user:
- Matched blueprint and recommended modules
- Custom requirements identified
- Questions that need answering

### 2. Plan — Design the Solution

Once requirements are clear:
```
odoo_design_solution(requirements=<analyzed_requirements>, user_answers=<answers>)
```

Present the phased plan in business language:
- Phase 1: Core modules and company setup
- Phase 2: Custom fields and views
- Phase 3: Automations and integrations
- Phase 4: Data import and user setup

Validate before executing:
```
odoo_validate_plan(plan=<designed_plan>)
```

### 3. Build — Execute the Plan

**Delegate to the odoo-executor agent** for each phase:
- The executor creates snapshots before each mutation
- The executor reports progress step-by-step
- After each phase, the **odoo-reviewer agent** validates the results

If code generation is needed:
```
odoo_generate_addon(name=<module_name>, models=<specs>, ...)
```

### 4. Verify — Confirm Everything Works

After all phases complete:
- Run `odoo_diagnostics_health_check`
- Walk through key workflows with the user
- Confirm the setup matches their expectations

## Key Principles

- **Always snapshot before changes** — the executor handles this, but verify
- **Present plans in business language** — avoid Odoo jargon with non-technical users
- **One phase at a time** — get user approval between phases
- **Blueprint first** — if an industry blueprint matches, start from there
- **Configuration over code** — prefer `x_` fields over custom modules when possible
