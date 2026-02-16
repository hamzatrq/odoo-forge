# Lovable for Odoo — System Design

**Date:** 2026-02-17
**Status:** Approved
**Goal:** Transform OdooForge from a tool library (71 MCP tools) into an intelligent system where non-technical business owners can describe their business in plain English and get a fully configured Odoo instance.

## Architecture Overview

Four layers stacked on the existing 71 tools, each independently valuable:

```
┌─────────────────────────────────────────────────────┐
│  User (via Claude Desktop / Cursor)                 │
│  "I run a bakery with 3 locations and delivery"     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  Claude (Primary Orchestrator)                       │
│  Guided by MCP Prompts (Layer 4)                     │
│  Informed by Domain Knowledge (Layer 1)              │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  OdooForge MCP Server (single process)               │
│                                                       │
│  Layer 3: Planning Tools                              │
│    odoo_analyze_requirements                          │
│    odoo_design_solution                               │
│    odoo_validate_plan                                 │
│                                                       │
│  Layer 2: Workflow Tools                              │
│    odoo_setup_business    odoo_create_feature          │
│    odoo_generate_addon    odoo_create_dashboard        │
│    odoo_setup_integration odoo_migrate_data            │
│    (each internally chains Layer 0 tools)             │
│                                                       │
│  Layer 1: Domain Knowledge (MCP Resources)            │
│    odoo://knowledge/modules                            │
│    odoo://knowledge/dictionary                         │
│    odoo://knowledge/patterns                           │
│    odoo://knowledge/best-practices                     │
│    odoo://knowledge/blueprints/{industry}              │
│                                                       │
│  Layer 0: Core Tools (existing 71)                    │
│    schema, views, records, automation, modules...     │
└───────────────────────────────────────────────────────┘
```

### Key Design Decisions

- **Single MCP server** — all layers live in the same `odooforge` package, sharing the existing `AppState` (RPC, Docker, PG, Cache). No separate processes.
- **Claude remains orchestrator** — we never build our own LLM routing. Claude reads MCP resources, picks tools, handles user conversation.
- **Layers are independent** — Layer 1 (knowledge) works without Layer 2 (workflows). Ship incrementally.
- **Workflow tools are deterministic** — they encode Odoo expertise as Python logic (correct ordering, dependency resolution, validation). No internal LLM calls.
- **Dual distribution** — MCP Prompts for all clients, Claude Code Skills as a bonus for CC users.

---

## Layer 1: Domain Knowledge (MCP Resources)

Static and dynamic knowledge that transforms Claude from "general AI that knows some Odoo" into "Odoo expert that speaks business language."

### Resource Groups

**1. Module Catalog** (`odoo://knowledge/modules`)

~200 Odoo 18 modules mapped to business language with dependency chains.

```
Business Need              → Odoo Modules
─────────────────────────────────────────
"Track inventory"          → stock, stock_account
"Sell online"              → website, website_sale, payment
"Manage employees"         → hr, hr_holidays, hr_attendance
"Send invoices"            → account, account_payment
"Track projects"           → project, project_todo
"Customer relationships"   → crm, crm_iap_mine
```

**2. Business-to-Odoo Dictionary** (`odoo://knowledge/dictionary`)

~150 business concept mappings.

```
Business Term    → Odoo Model            Notes
──────────────────────────────────────────────────
Customer         → res.partner           type='contact'
Vendor/Supplier  → res.partner           supplier_rank > 0
Invoice          → account.move          move_type='out_invoice'
Product          → product.template      (not product.product)
Sales Order      → sale.order
Employee         → hr.employee           linked to res.partner
Warehouse        → stock.warehouse
Price List       → product.pricelist
Tax              → account.tax
```

**3. Data Model Patterns** (`odoo://knowledge/patterns`)

~30 patterns covering the most common customization scenarios.

```yaml
pattern: trackable-custom-model
description: "A new model with messaging, activity tracking, and stages"
approach: code_generation
ingredients:
  - _inherit: [mail.thread, mail.activity.mixin]
  - stage_id: Many2one → custom stage model
  - kanban view with stage grouping
  - activity view
  - security: ir.model.access + ir.rule

pattern: partner-extension
description: "Add custom fields to contacts/companies"
approach: configuration
ingredients:
  - x_ prefixed fields on res.partner
  - form view inheritance via XPath
  - optional: smart button linking to related records
```

Each pattern specifies whether it can be done via configuration (existing tools) or requires code generation.

**4. Industry Blueprints** (`odoo://knowledge/blueprints/{industry}`)

~15-20 industry blueprints. Richer than current recipes — include data model designs, not just module lists.

```yaml
blueprint: bakery
modules: [point_of_sale, stock, mrp, hr, account, ...]
models:
  - extend res.partner:
      x_loyalty_tier: Selection (bronze/silver/gold)
      x_dietary_preferences: Many2many → custom tag model
  - extend product.template:
      x_allergens: Many2many → custom allergen model
      x_prep_time_minutes: Integer
      x_is_made_to_order: Boolean
views:
  - POS product card: show allergens + prep time
  - Customer form: loyalty tier + dietary prefs
automations:
  - "When loyalty_tier changes → send notification email"
  - "When stock < reorder_point → create manufacturing order"
multi_company:
  - 3 locations as branches under parent company
  - shared product catalog, separate stock
```

**5. Best Practices** (`odoo://knowledge/best-practices`)

Odoo conventions and guidelines for field naming, model design, security, views, reports.

### Static vs Dynamic

| Resource | Type | Rationale |
|----------|------|-----------|
| Module catalog | Static | Baked into package, versioned with Odoo 18 |
| Business dictionary | Static | Standard Odoo models don't change |
| Model patterns | Static | Design patterns are stable |
| Industry blueprints | Static | Curated reference designs |
| Best practices | Static | Conventions are stable |
| Installed modules | Dynamic | Read from running instance via existing cache |
| Available models/fields | Dynamic | Read from running instance via existing tools |

Static resources live as structured YAML files in `src/odooforge/knowledge/`. Dynamic data already exists via `LiveStateCache` and existing tools.

---

## Layer 2: Workflow Tools (Composite Operations)

High-level tools that chain multiple Layer 0 tools in the correct order with snapshot-based rollback.

### Core Workflow Tools

**`odoo_setup_business`** — Full business setup from blueprint or custom spec.

Input: blueprint name (or custom spec), company name, locations, dry_run flag.
Internal sequence: snapshot → company config → module install → settings → custom models → custom fields → views → automations → email templates → roles → health check.
Output: complete report of what was created, with snapshot ID for rollback.

**`odoo_create_feature`** — Build a complete feature in one call.

Input: feature name, target model, field definitions, view modifications, optional automation.
Internal sequence: create fields → read current views → modify form view → modify tree view → create automation → verify.
Output: fields created, views modified, automation ID.

**`odoo_generate_addon`** — Generate a complete installable Odoo module as code.

Input: module name, model specs (fields, methods, mixins), view types, security groups, deploy mode (hot_reload or git_scaffold).
Internal sequence: generate __manifest__.py → models/*.py → views/*.xml → security CSVs → data XMLs → __init__.py → deploy.
Output: file list, module path, installation status.

**`odoo_create_dashboard`** — Build a management dashboard.

Input: dashboard name, metric definitions (model, measure, filter).
Internal sequence: create dashboard action → set up saved filters → create menu item → configure graphs/pivots.

**`odoo_setup_integration`** — Configure external connections.

Input: integration type (email, payment, shipping), provider, credentials.
Internal sequence: chains relevant config tools with validation and testing.

### Design Principles

- **Snapshot before mutate** — every workflow creates a snapshot first.
- **Step-by-step reporting** — returns what succeeded, what failed, where to rollback.
- **Dry-run mode** — every workflow supports `dry_run=true` to preview without executing.
- **Idempotent where possible** — re-running skips already-completed steps.
- **No LLM calls** — deterministic Python. Intelligence is in ordering and defaults.

---

## Layer 3: Planning Tools

Tools that bridge natural language to structured execution plans. They analyze, design, and validate — but don't execute.

### Planning Tools

**`odoo_analyze_requirements`** — Parse business description into structured Odoo requirements.

Input: natural language business description.
Output: matched industry/blueprint, modules needed (with reasons), custom requirements (with approach: configuration vs code generation), infrastructure needs (multi-company, locations), gaps/ambiguities, and questions for the user.

Uses pattern matching against Layer 1 knowledge base — not LLM calls.

**`odoo_design_solution`** — Turn requirements into a phased execution plan (DAG).

Input: analyzed requirements + user answers to clarifying questions.
Output: phased plan with dependency ordering, parallelization hints, tool calls per step, snapshot points, and estimated complexity.

Plans are DAGs — independent phases can run in parallel. Each step specifies the exact Layer 2 workflow tool or Layer 0 tool to call with parameters.

**`odoo_validate_plan`** — Pre-flight check against the live Odoo instance.

Input: execution plan.
Output: validation results — module compatibility, field conflicts, dependency ordering, resource requirements, existing state conflicts.

Checks against the live instance using `LiveStateCache` and core tools.

### Planning Flow

```
User describes business
  → odoo_analyze_requirements (NL → structured requirements)
  → Claude presents questions_for_user to user
  → User answers
  → odoo_design_solution (requirements → phased plan)
  → Claude presents plan in business language
  → User approves
  → odoo_validate_plan (pre-flight checks)
  → Execute via Layer 2 workflow tools
```

---

## Layer 4a: MCP Prompts (All MCP Clients)

Workflow templates injected into Claude's context that guide the correct usage of Layers 1-3.

### Prompts

**`business-setup`** — Guided workflow for full business setup.
Steps: understand → analyze requirements → present questions → design solution → validate → confirm with user → execute phase by phase → verify.

**`feature-builder`** — Add a custom feature to existing setup.
Steps: understand need → check dictionary/patterns → decide configuration vs code gen → execute → verify → iterate.

**`module-generator`** — Generate a custom Odoo addon.
Steps: gather requirements (models, views, security, automations) → design module structure → present for approval → generate → deploy → test.

**`troubleshooter`** — Diagnose and fix Odoo issues.
Steps: health check + logs → identify issue → explain in plain language → snapshot → fix → verify → advise prevention.

---

## Layer 4b: Claude Code Skills (Claude Code Users)

Odoo-specific process skills that extend Claude Code's existing skill system.

**`odoo-brainstorm`** — Extends brainstorming with Odoo-specific exploration: module discovery, blueprint matching, configuration-vs-code decision, existing data/model awareness.

**`odoo-architect`** — Guides Odoo data model design: naming conventions, mandatory checklist (mail.thread, multi-company, stages, sequences), field conventions.

**`odoo-debug`** — Odoo-specific debugging: log reading patterns, common error → fix mappings, module state checks, nuclear options with user confirmation.

---

## Implementation Phases

Each phase ships standalone value. No phase depends on a later phase to be useful.

### Phase 1: Domain Knowledge (Layer 1)

```
Deliverables:
  src/odooforge/knowledge/
    modules.yaml, dictionary.yaml, patterns.yaml,
    best_practices.yaml, blueprints/*.yaml
  MCP resource handlers in server.py
  Tests for resource loading

Effort: Medium (content curation + resource registration)
Impact: High — Claude becomes an Odoo expert
Depends on: Nothing
```

### Phase 2: MCP Prompts (Layer 4a)

```
Deliverables:
  MCP prompt registrations in server.py
    business-setup, feature-builder, module-generator, troubleshooter
  Tests for prompt availability

Effort: Low (prompt engineering, no tool code)
Impact: High — structured workflows for 4 main use cases
Depends on: Phase 1
```

### Phase 3: Planning Tools (Layer 3)

```
Deliverables:
  src/odooforge/tools/planning.py
  src/odooforge/planning/
    requirement_parser.py, solution_designer.py,
    plan_validator.py, dependency_resolver.py
  Tests for each planning function

Effort: High (parsing logic, plan generation, validation)
Impact: High — users see clear plans before execution
Depends on: Phase 1
```

### Phase 4: Workflow Tools (Layer 2)

```
Deliverables:
  src/odooforge/tools/workflows.py
  src/odooforge/workflows/
    executor.py, rollback.py, progress.py
  Tests for each workflow

Effort: High (orchestration, error handling, rollback)
Impact: Very high — "one prompt → full business"
Depends on: Phase 3
```

### Phase 5: Code Generation (Layer 2, odoo_generate_addon)

```
Deliverables:
  src/odooforge/tools/codegen.py
  src/odooforge/codegen/
    templates/*.j2 (manifest, model, views, security, init)
    scaffold.py, model_generator.py, view_generator.py,
    security_generator.py, deployer.py
  Tests for generation + validation

Effort: Very high (template system, code generation, deployment)
Impact: High — enables "build me a custom app" scenarios
Depends on: Phase 4
```

### Phase 6: Claude Code Skills (Layer 4b) — Parallel

```
Deliverables:
  skills/odoo-brainstorm.md
  skills/odoo-architect.md
  skills/odoo-debug.md

Effort: Low (documentation/prompt writing)
Impact: Medium — process discipline for Claude Code users
Depends on: Nothing (build alongside any phase)
```

### Value Curve

```
Phase 1 ████████░░░░░░░░░░░░  "Claude knows Odoo"
Phase 2 ████████████░░░░░░░░  "Claude follows workflows"
Phase 3 ████████████████░░░░  "Claude plans before acting"
Phase 4 ██████████████████░░  "One prompt → full business"
Phase 5 ████████████████████  "Custom modules from English"
```
