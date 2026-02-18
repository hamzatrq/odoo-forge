# OdooForge Plugin Architecture — Design Document

**Date:** 2026-02-18
**Status:** Draft
**Supersedes:** `2026-02-17-lovable-for-odoo-design.md` (extends, does not invalidate)
**Goal:** Transform OdooForge from "MCP server + some skills" into a comprehensive Claude Code Plugin that serves as an ongoing AI layer for Odoo — not just setup, but the permanent interface between business users and their ERP.

## Vision

**Before:** User installs OdooForge, sets up their Odoo, then… stops using it.
**After:** OdooForge is always there — discovering, planning, building, populating, analyzing, fixing, evolving. It's the AI layer that makes Odoo accessible to non-technical business owners permanently.

### The Lifecycle

```
Discover → Plan → Build → Populate → Analyze → Fix → Evolve
   ↑                                                    │
   └────────────────────────────────────────────────────┘
```

1. **Discover** — "What can Odoo do for my bakery?"
2. **Plan** — "Here's a phased setup plan with 3 stages"
3. **Build** — Configure modules, create custom fields, generate addons
4. **Populate** — Import data, create records, set up users
5. **Analyze** — "Show me sales by location this month"
6. **Fix** — "Why can't I create invoices?" → diagnose, snapshot, repair
7. **Evolve** — "We added delivery, what do we need?" → back to Discover

---

## Architecture: 5 Extension Points

Claude Code provides 5 extension mechanisms. OdooForge uses all of them:

```
┌─────────────────────────────────────────────────────────────┐
│  OdooForge Claude Code Plugin                               │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 6 Skills     │  │ 4 Subagents  │  │ Safety Hooks │      │
│  │ (workflows)  │  │ (specialists)│  │ (guardrails) │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│  ┌──────▼──────────────────▼──────────────────▼──────┐      │
│  │  MCP Server (79 tools, 6 resources, 4 prompts)    │      │
│  └───────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 1. MCP Server (existing — enhance)

The foundation. 79 tools across 20 categories, 6 resources, 4 prompts. Already built and shipping. Enhancements:

- **Tool annotations** — add `readOnlyHint`, `destructiveHint`, `costHint` to every tool so Claude can reason about safety without needing hooks for basic cases
- **Streamable HTTP transport** — add alongside stdio for web-based clients
- **Resource subscriptions** — notify clients when live state changes (module installs, schema changes)

### 2. Skills (expand from 3 → 6)

Skills run in the main conversation context, guiding Claude through structured workflows. They're the "process knowledge" layer.

**Existing (keep, enhance):**

| Skill | Purpose |
|-------|---------|
| `/odoo-brainstorm` | Explore ideas, discover modules, match blueprints |
| `/odoo-architect` | Design data models with Odoo conventions |
| `/odoo-debug` | Diagnose issues with error mapping and snapshots |

**New:**

| Skill | Purpose | Lifecycle Phase |
|-------|---------|-----------------|
| `/odoo-setup` | Full business deployment from natural language — orchestrates the Discover→Plan→Build flow | Build |
| `/odoo-data` | Import, create, and manage business data — CSV imports, bulk record creation, data migration | Populate |
| `/odoo-report` | Build dashboards, define KPIs, create custom reports, analyze business data | Analyze |

**Skill design principles:**
- Skills are process guides, not tool wrappers — they tell Claude *when* and *why* to use tools, not just *how*
- Each skill maps to a lifecycle phase
- Skills can specify `context: fork` to run as subagents for long-running operations
- Skills reference MCP tools by name, keeping tool logic in the server
- User-invocable via slash commands

### 3. Subagents (new — 4 specialists)

Subagents run in isolated contexts with their own system prompts, tool permissions, and memory. They're the "expert delegation" layer.

| Agent | Role | Key Tools | When Dispatched |
|-------|------|-----------|-----------------|
| `odoo-explorer` | Codebase & instance scout | Read-only MCP tools, Grep, Glob | Before planning — gathers instance state, installed modules, existing customizations |
| `odoo-executor` | Plan execution engine | All MCP tools (write access) | After plan approval — executes step-by-step with snapshots |
| `odoo-reviewer` | Post-execution validator | Read-only MCP tools, health check | After execution — validates results, checks for regressions |
| `odoo-analyst` | Data analysis & reporting | SQL tools, record search, dashboard tools | On-demand — analyzes business data, generates insights |

**Agent design principles:**
- Each agent has a constrained tool set (principle of least privilege)
- `odoo-executor` always creates a snapshot before mutating
- `odoo-reviewer` runs after every execution phase — automatic quality gate
- Agents can have persistent memory (project scope) to remember instance state across sessions
- `maxTurns` limits prevent runaway execution
- `permissionMode: allowAll` for read-only agents, `byToolPolicy` for write agents

**Agent frontmatter example (odoo-executor):**

```yaml
---
name: odoo-executor
description: Executes OdooForge plans step-by-step with snapshot safety
model: sonnet
maxTurns: 50
permissionMode: byToolPolicy
mcpServers:
  - odooforge
tools:
  - mcp__odooforge__*
  - Read
  - Glob
disallowedTools:
  - Bash
  - Write
  - Edit
memory:
  project: true
hooks:
  preToolUse:
    - type: prompt
      matcher: "mcp__odooforge__odoo_db_drop|mcp__odooforge__odoo_module_uninstall"
      prompt: "DANGER: This is a destructive operation. Verify the user has explicitly approved this specific action. If not, BLOCK."
---
```

### 4. Hooks (new — safety guardrails)

Hooks intercept tool calls at lifecycle events. They're the "safety" layer.

**PreToolUse hooks:**

| Hook | Matcher | Action |
|------|---------|--------|
| Snapshot reminder | `mcp__odooforge__odoo_schema_*`, `mcp__odooforge__odoo_module_*` | Prompt: "Have you created a snapshot? If not, create one first." |
| Destructive guard | `mcp__odooforge__odoo_db_drop`, `mcp__odooforge__odoo_record_delete` | Prompt: "This will permanently delete data. Confirm the user explicitly requested this." |
| Production check | `mcp__odooforge__odoo_*` (write ops) | Command: check if `ODOO_URL` points to a production domain, warn if so |

**PostToolUse hooks:**

| Hook | Matcher | Action |
|------|---------|--------|
| Health check after install | `mcp__odooforge__odoo_module_install` | Prompt: "Module installed. Run health check to verify system stability." |
| Cache invalidation | `mcp__odooforge__odoo_schema_*`, `mcp__odooforge__odoo_view_*` | Command: log what changed for the reviewer agent |

**Stop hooks:**

| Hook | Action |
|------|--------|
| Session summary | Prompt: "Before ending, summarize what was changed in this session and suggest next steps." |

### 5. Plugin Packaging (new)

Bundle everything into a single installable unit via `plugin.json`:

```json
{
  "name": "odooforge",
  "version": "0.3.0",
  "description": "AI-First ERP Configuration Engine for Odoo 18",
  "skills": [
    "skills/odoo-brainstorm",
    "skills/odoo-architect",
    "skills/odoo-debug",
    "skills/odoo-setup",
    "skills/odoo-data",
    "skills/odoo-report"
  ],
  "agents": [
    "agents/odoo-explorer.md",
    "agents/odoo-executor.md",
    "agents/odoo-reviewer.md",
    "agents/odoo-analyst.md"
  ],
  "mcpServers": {
    "odooforge": {
      "command": "uvx",
      "args": ["odooforge"],
      "env": {
        "ODOO_URL": "${ODOO_URL}",
        "ODOO_DEFAULT_DB": "${ODOO_DEFAULT_DB}",
        "ODOO_ADMIN_USER": "${ODOO_ADMIN_USER}",
        "ODOO_ADMIN_PASSWORD": "${ODOO_ADMIN_PASSWORD}",
        "POSTGRES_HOST": "${POSTGRES_HOST}",
        "POSTGRES_PORT": "${POSTGRES_PORT}",
        "POSTGRES_USER": "${POSTGRES_USER}",
        "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD}"
      }
    }
  },
  "hooks": {
    "preToolUse": [...],
    "postToolUse": [...],
    "stop": [...]
  }
}
```

**Distribution:** Published to the Claude Code plugin marketplace. Users install with one command, get everything — MCP server, skills, agents, hooks.

**`odooforge init` evolution:** For non-plugin users (Cursor, Windsurf, Claude Desktop), `odooforge init` continues to scaffold the workspace. For Claude Code plugin users, `odooforge init` detects the plugin and only creates `.env` and `docker/`.

---

## How It All Works Together

### Example: "I run a bakery with 3 locations and delivery"

```
1. User invokes /odoo-setup
   → Skill guides Claude through the Discover→Plan→Build flow

2. DISCOVER: Skill dispatches odoo-explorer subagent
   → Explorer reads MCP resources (blueprints, modules, dictionary)
   → Explorer checks live instance state (existing modules, data)
   → Returns: "bakery blueprint matches, 12 modules needed, instance is fresh"

3. PLAN: Skill uses planning tools (analyze_requirements, design_solution, validate_plan)
   → Presents phased plan to user in business language
   → User approves

4. BUILD: Skill dispatches odoo-executor subagent
   → PreToolUse hook: "Creating snapshot before execution"
   → Executor runs phase by phase (modules → config → custom fields → views → automations)
   → PostToolUse hooks log each change

5. REVIEW: Skill dispatches odoo-reviewer subagent
   → Reviewer runs health check, validates all customizations
   → Reports: "All 12 modules installed, 8 custom fields created, 3 views modified, health: OK"

6. POPULATE: User says "I have a spreadsheet of products"
   → /odoo-data skill guides CSV import
   → odoo-executor handles the import with validation

7. ANALYZE: Two weeks later, user says "How are sales?"
   → /odoo-report skill dispatches odoo-analyst
   → Analyst queries sales data, builds dashboard
   → Returns insights in business language

8. FIX: "I can't create invoices"
   → /odoo-debug skill activates
   → Reads logs, checks module state, identifies missing config
   → Creates snapshot, applies fix, verifies

9. EVOLVE: "We're adding catering services"
   → Back to /odoo-brainstorm → /odoo-setup
   → Lifecycle continues
```

---

## Implementation Phases

### Phase 1: Subagents (high impact, low effort)

Create 4 agent definition files in `.claude/agents/`. No code changes to the MCP server.

**Deliverables:**
- `.claude/agents/odoo-explorer.md`
- `.claude/agents/odoo-executor.md`
- `.claude/agents/odoo-reviewer.md`
- `.claude/agents/odoo-analyst.md`
- Update `odooforge init` to scaffold agents
- Tests for agent file content and structure

**Effort:** Low — markdown files with YAML frontmatter
**Impact:** High — enables specialist delegation

### Phase 2: New Skills (medium effort)

Create 3 new skills that orchestrate subagents and MCP tools.

**Deliverables:**
- `.claude/skills/odoo-setup/SKILL.md`
- `.claude/skills/odoo-data/SKILL.md`
- `.claude/skills/odoo-report/SKILL.md`
- Update existing skills to reference subagents
- Update `odooforge init` to scaffold new skills
- Tests

**Effort:** Medium — skill design requires careful workflow thinking
**Impact:** High — covers all lifecycle phases

### Phase 3: Safety Hooks (low effort)

Define hook configurations for safety guardrails.

**Deliverables:**
- Hook definitions in plugin config / settings
- Documentation on what each hook does
- Update `odooforge init` to scaffold hook config

**Effort:** Low — configuration, not code
**Impact:** Medium — prevents accidents, builds trust

### Phase 4: MCP Server Enhancements (medium effort)

Add tool annotations, improve resource handling.

**Deliverables:**
- Tool annotations on all 79 tools
- Streamable HTTP transport option
- Resource subscription support (if FastMCP supports it)

**Effort:** Medium — touches many tool definitions
**Impact:** Medium — better safety reasoning, broader client support

### Phase 5: Plugin Packaging (low effort, depends on Phase 1-3)

Bundle everything into a `plugin.json` for marketplace distribution.

**Deliverables:**
- `plugin.json` manifest
- Plugin marketplace submission
- Documentation for plugin vs non-plugin installation

**Effort:** Low — packaging, not new functionality
**Impact:** High — one-command install for Claude Code users

### Value Timeline

```
Phase 1 (Subagents)    ████████░░░░░░  Expert delegation
Phase 2 (Skills)       ████████████░░  Full lifecycle coverage
Phase 3 (Hooks)        ██████████████  Safety guardrails
Phase 4 (MCP enhance)  ██████████████  Better tool reasoning
Phase 5 (Plugin)       ██████████████  One-command install
```

---

## File Structure (target)

```
src/odooforge/
├── data/
│   ├── skills/
│   │   ├── odoo-brainstorm/SKILL.md
│   │   ├── odoo-architect/SKILL.md
│   │   ├── odoo-debug/SKILL.md
│   │   ├── odoo-setup/SKILL.md      # NEW
│   │   ├── odoo-data/SKILL.md       # NEW
│   │   └── odoo-report/SKILL.md     # NEW
│   ├── agents/                       # NEW
│   │   ├── odoo-explorer.md
│   │   ├── odoo-executor.md
│   │   ├── odoo-reviewer.md
│   │   └── odoo-analyst.md
│   └── templates/                    # existing
│       ├── CLAUDE.md, .env, docker/, mcp configs
│       └── plugin.json               # NEW
├── init.py                           # updated to scaffold agents
├── cli.py
├── server.py                         # tool annotations added
└── ...existing layers...
```

---

## What This Is NOT

- **Not an autonomous agent framework** — Claude remains the orchestrator. Subagents are specialists dispatched by Claude, not independent actors.
- **Not a replacement for the MCP server** — the 79 tools remain the foundation. Skills and agents are orchestration layers on top.
- **Not locked to Claude Code** — MCP server + prompts work in any MCP client. Skills/agents/hooks are Claude Code bonuses.
- **Not a one-time setup tool** — the whole point is the ongoing lifecycle. OdooForge stays valuable after day 1.

---

## Open Questions

1. **Plugin marketplace readiness** — Is the Claude Code plugin marketplace accepting submissions? If not, we distribute as `odooforge init` scaffolding (current approach) until it is.
2. **Agent memory scope** — Should agents use project-level persistent memory to remember instance state across sessions? Useful but adds complexity.
3. **Hook complexity** — Start with prompt-based hooks (simple) or command-based hooks (more powerful but require shell scripts)?
4. **Streamable HTTP** — Does FastMCP support streamable HTTP transport? If not, defer to a later phase.
