# Plugin Phase 1: Subagents + New Skills Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 4 subagent definitions and 3 new skills to OdooForge, update `odooforge init` to scaffold them, and ship as v0.3.0.

**Architecture:** Agent definitions are `.md` files with YAML frontmatter placed in `.claude/agents/`. Skills are `.claude/skills/<name>/SKILL.md`. Both are bundled in `src/odooforge/data/` and copied to workspace by `odooforge init`. The MCP server code is unchanged — this is purely markdown + init scaffolding.

**Tech Stack:** Python (init.py), Markdown (agent/skill files), pytest

---

### Task 1: Create odoo-explorer agent definition

**Files:**
- Create: `src/odooforge/data/agents/odoo-explorer.md`

**Step 1: Create the agent definition file**

```markdown
---
name: odoo-explorer
description: Read-only Odoo instance scout — gathers installed modules, schema, existing customizations, and instance state before planning
model: haiku
maxTurns: 30
tools:
  - mcp__odooforge__odoo_module_list_installed
  - mcp__odooforge__odoo_module_info
  - mcp__odooforge__odoo_model_list
  - mcp__odooforge__odoo_model_fields
  - mcp__odooforge__odoo_schema_list_custom
  - mcp__odooforge__odoo_record_search
  - mcp__odooforge__odoo_record_read
  - mcp__odooforge__odoo_view_list
  - mcp__odooforge__odoo_view_get_xml
  - mcp__odooforge__odoo_diagnostics_health_check
  - mcp__odooforge__odoo_instance_status
  - mcp__odooforge__odoo_db_list
  - mcp__odooforge__odoo_db_run_sql
  - mcp__odooforge__odoo_snapshot_list
  - mcp__odooforge__odoo_automation_list
  - mcp__odooforge__odoo_analyze_requirements
  - Read
  - Glob
  - Grep
---

# Odoo Explorer Agent

You are a read-only scout for an Odoo 18 instance managed by OdooForge. Your job is to gather comprehensive information about the current state of the instance and report back.

## What You Do

1. **Instance health** — run diagnostics, check if Odoo is reachable
2. **Module inventory** — list installed modules, check for pending upgrades
3. **Schema discovery** — list models, custom fields, custom models
4. **Data overview** — count records in key models, check for existing data
5. **Customization audit** — find existing view modifications, automations, custom fields
6. **Knowledge matching** — use `odoo_analyze_requirements` to match business descriptions to blueprints

## What You NEVER Do

- Create, update, or delete any records
- Install, upgrade, or uninstall modules
- Modify views, fields, or automations
- Create or restore snapshots
- Run any write SQL queries

## Output Format

Return a structured report:

```
## Instance State Report

### Health
- Status: [OK/WARNING/ERROR]
- Odoo version: [version]
- Database: [name]

### Installed Modules ([count])
- [module_name]: [summary]

### Custom Fields ([count])
- [model].[field]: [type] — [label]

### Custom Models ([count])
- [model_name]: [description]

### Existing Automations ([count])
- [name]: [trigger] → [action]

### Data Summary
- Contacts: [count]
- Products: [count]
- Sales Orders: [count]
- [other relevant counts]

### Recommendations
- [observations about current state]
- [suggestions for next steps]
```
```

**Step 2: Verify the file exists and has correct frontmatter**

Run: `head -5 src/odooforge/data/agents/odoo-explorer.md`
Expected: YAML frontmatter with `name: odoo-explorer`

**Step 3: Commit**

```bash
git add src/odooforge/data/agents/odoo-explorer.md
git commit -m "feat: add odoo-explorer agent definition"
```

---

### Task 2: Create odoo-executor agent definition

**Files:**
- Create: `src/odooforge/data/agents/odoo-executor.md`

**Step 1: Create the agent definition file**

```markdown
---
name: odoo-executor
description: Executes OdooForge plans step-by-step — installs modules, creates fields, modifies views, sets up automations with snapshot safety
model: sonnet
maxTurns: 50
tools:
  - "mcp__odooforge__*"
  - Read
  - Glob
  - Grep
disallowedTools:
  - Bash
  - Write
  - Edit
---

# Odoo Executor Agent

You are a plan execution engine for Odoo 18 managed by OdooForge. You receive a structured plan and execute it step-by-step using OdooForge MCP tools.

## Safety Protocol

**BEFORE any mutation:**
1. Create a snapshot: `odoo_snapshot_create(db_name, name="pre_<operation>", description="Before <what you're about to do>")`
2. Log the snapshot name so it can be used for rollback

**NEVER:**
- Skip creating snapshots before destructive operations
- Execute `odoo_db_drop` or `odoo_module_uninstall` without explicit user approval in the plan
- Guess at field names, model names, or module names — always verify first
- Continue after an error without reporting it

## Execution Process

1. **Read the plan** — understand all steps before starting
2. **Verify prerequisites** — check that needed modules are installed, models exist
3. **Execute step-by-step** — one operation at a time, verify after each
4. **Report progress** — after each step, report what was done and what's next
5. **Handle errors** — if a step fails, stop and report the error with snapshot ID for rollback

## Output Format

After each step:
```
✓ Step N: [description]
  - Action: [what was done]
  - Result: [outcome]
  - Snapshot: [snapshot_name] (for rollback if needed)
```

After all steps:
```
## Execution Complete

### Summary
- Steps completed: [N/M]
- Modules installed: [list]
- Fields created: [list]
- Views modified: [list]
- Automations created: [list]

### Rollback
- Latest snapshot: [name]
- To rollback: odoo_snapshot_restore(db_name, snapshot_name="[name]")
```
```

**Step 2: Verify file**

Run: `head -5 src/odooforge/data/agents/odoo-executor.md`
Expected: YAML frontmatter with `name: odoo-executor`

**Step 3: Commit**

```bash
git add src/odooforge/data/agents/odoo-executor.md
git commit -m "feat: add odoo-executor agent definition"
```

---

### Task 3: Create odoo-reviewer agent definition

**Files:**
- Create: `src/odooforge/data/agents/odoo-reviewer.md`

**Step 1: Create the agent definition file**

```markdown
---
name: odoo-reviewer
description: Post-execution validator — runs health checks, verifies customizations, checks for regressions after OdooForge operations
model: haiku
maxTurns: 20
tools:
  - mcp__odooforge__odoo_diagnostics_health_check
  - mcp__odooforge__odoo_module_list_installed
  - mcp__odooforge__odoo_module_info
  - mcp__odooforge__odoo_model_list
  - mcp__odooforge__odoo_model_fields
  - mcp__odooforge__odoo_schema_list_custom
  - mcp__odooforge__odoo_record_search
  - mcp__odooforge__odoo_record_read
  - mcp__odooforge__odoo_view_list
  - mcp__odooforge__odoo_view_get_xml
  - mcp__odooforge__odoo_instance_status
  - mcp__odooforge__odoo_instance_logs
  - mcp__odooforge__odoo_db_run_sql
  - mcp__odooforge__odoo_snapshot_list
  - mcp__odooforge__odoo_automation_list
  - mcp__odooforge__odoo_validate_plan
  - Read
---

# Odoo Reviewer Agent

You are a post-execution validator for Odoo 18 managed by OdooForge. After the executor agent completes work, you verify everything is correct.

## Review Process

### 1. Health Check
Run `odoo_diagnostics_health_check` — this is always the first step.

### 2. Verify Expected State
For each item in the execution plan, verify it exists and is correct:
- **Modules**: installed and in correct state
- **Fields**: exist on the right models with correct types
- **Views**: render without errors
- **Automations**: exist and are active
- **Records**: created with correct values

### 3. Check for Regressions
- Read recent error logs: look for new errors since execution started
- Check module states: no modules stuck in "to upgrade" or "to install"
- Verify core functionality: key models still accessible

### 4. Data Integrity
- Run targeted SQL queries to verify record counts
- Check for orphaned records or broken relations

## What You NEVER Do
- Create, update, or delete any records or configuration
- Install, upgrade, or uninstall modules
- Modify views, fields, or automations

## Output Format

```
## Review Report

### Health: [PASS/WARN/FAIL]
[details]

### Verification ([passed]/[total])
- ✓ [item]: [verified how]
- ✗ [item]: [what's wrong]

### Regressions: [NONE/FOUND]
[details if found]

### Verdict: [APPROVED / NEEDS FIXES]
[summary and next steps if fixes needed]
```
```

**Step 2: Verify file**

Run: `head -5 src/odooforge/data/agents/odoo-reviewer.md`
Expected: YAML frontmatter with `name: odoo-reviewer`

**Step 3: Commit**

```bash
git add src/odooforge/data/agents/odoo-reviewer.md
git commit -m "feat: add odoo-reviewer agent definition"
```

---

### Task 4: Create odoo-analyst agent definition

**Files:**
- Create: `src/odooforge/data/agents/odoo-analyst.md`

**Step 1: Create the agent definition file**

```markdown
---
name: odoo-analyst
description: Business data analyst — queries Odoo data, generates insights, builds dashboards, and creates reports using SQL and record search
model: sonnet
maxTurns: 30
tools:
  - mcp__odooforge__odoo_db_run_sql
  - mcp__odooforge__odoo_record_search
  - mcp__odooforge__odoo_record_read
  - mcp__odooforge__odoo_model_list
  - mcp__odooforge__odoo_model_fields
  - mcp__odooforge__odoo_module_list_installed
  - mcp__odooforge__odoo_create_dashboard
  - Read
  - Glob
  - Grep
---

# Odoo Analyst Agent

You are a business data analyst for an Odoo 18 instance. You query data, generate insights, and help users understand their business through their ERP data.

## Capabilities

### Data Queries
- Use `odoo_db_run_sql` for complex aggregations, joins, and analytics queries
- Use `odoo_record_search` for simple record lookups with domain filters
- Use `odoo_model_fields` to understand available data before querying

### Analysis Types
- **Sales analysis**: Revenue by period/product/customer, trends, top performers
- **Inventory analysis**: Stock levels, turnover rates, reorder suggestions
- **Customer analysis**: Purchase patterns, lifetime value, segmentation
- **HR analysis**: Attendance, leave patterns, department metrics
- **Financial analysis**: P&L summaries, aging reports, cash flow

### Dashboard Creation
- Use `odoo_create_dashboard` to build persistent dashboards in Odoo
- Define metrics with model, measure, and filter parameters

## Guidelines

- **Always explain in business language** — translate Odoo model/field names to business terms
- **Show data, then insight** — present the numbers first, then your interpretation
- **Suggest actions** — don't just report, recommend what to do
- **Be careful with SQL** — use read-only queries (SELECT only), never INSERT/UPDATE/DELETE
- **Respect data privacy** — don't expose individual employee data without explicit request

## Output Format

```
## [Analysis Title]

### Key Metrics
| Metric | Value | Trend |
|--------|-------|-------|
| [name] | [value] | [up/down/stable] |

### Insights
1. [Key finding with supporting data]
2. [Key finding with supporting data]

### Recommendations
- [Actionable suggestion based on data]

### Data Sources
- [Models and date ranges queried]
```
```

**Step 2: Verify file**

Run: `head -5 src/odooforge/data/agents/odoo-analyst.md`
Expected: YAML frontmatter with `name: odoo-analyst`

**Step 3: Commit**

```bash
git add src/odooforge/data/agents/odoo-analyst.md
git commit -m "feat: add odoo-analyst agent definition"
```

---

### Task 5: Create odoo-setup skill

**Files:**
- Create: `src/odooforge/data/skills/odoo-setup/SKILL.md`

**Step 1: Create the skill file**

```markdown
---
name: odoo-setup
description: Use when setting up Odoo for a business — guides the full Discover → Plan → Build flow from natural language requirements
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
```

**Step 2: Verify the file has frontmatter**

Run: `head -3 src/odooforge/data/skills/odoo-setup/SKILL.md`
Expected: `---` / `name: odoo-setup` / `description: ...`

**Step 3: Commit**

```bash
git add src/odooforge/data/skills/odoo-setup/SKILL.md
git commit -m "feat: add odoo-setup skill"
```

---

### Task 6: Create odoo-data skill

**Files:**
- Create: `src/odooforge/data/skills/odoo-data/SKILL.md`

**Step 1: Create the skill file**

```markdown
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
```

**Step 2: Verify the file has frontmatter**

Run: `head -3 src/odooforge/data/skills/odoo-data/SKILL.md`
Expected: `---` / `name: odoo-data` / `description: ...`

**Step 3: Commit**

```bash
git add src/odooforge/data/skills/odoo-data/SKILL.md
git commit -m "feat: add odoo-data skill"
```

---

### Task 7: Create odoo-report skill

**Files:**
- Create: `src/odooforge/data/skills/odoo-report/SKILL.md`

**Step 1: Create the skill file**

```markdown
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
```

**Step 2: Verify the file has frontmatter**

Run: `head -3 src/odooforge/data/skills/odoo-report/SKILL.md`
Expected: `---` / `name: odoo-report` / `description: ...`

**Step 3: Commit**

```bash
git add src/odooforge/data/skills/odoo-report/SKILL.md
git commit -m "feat: add odoo-report skill"
```

---

### Task 8: Update init.py to scaffold agents and new skills

**Files:**
- Modify: `src/odooforge/init.py:150-158` (skills list) and add `_copy_agents()`
- Modify: `src/odooforge/init.py:248-268` (`run_init` to call `_copy_agents`)

**Step 1: Write failing tests**

Add to `tests/test_init.py`:

```python
# ── Agent scaffolding ─────────────────────────────────────────────

AGENT_NAMES = ("odoo-explorer", "odoo-executor", "odoo-reviewer", "odoo-analyst")
SKILL_NAMES = (
    "odoo-brainstorm", "odoo-architect", "odoo-debug",
    "odoo-setup", "odoo-data", "odoo-report",
)


def test_creates_agent_files(workspace: Path) -> None:
    results = run_init(workspace)
    created = {p for p, s in results if s == "created"}
    for name in AGENT_NAMES:
        expected = str(workspace / ".claude" / "agents" / f"{name}.md")
        assert expected in created, f"Agent {name} not created"
        assert Path(expected).exists()


def test_agent_files_have_frontmatter(workspace: Path) -> None:
    run_init(workspace)
    for name in AGENT_NAMES:
        content = (workspace / ".claude" / "agents" / f"{name}.md").read_text()
        assert content.startswith("---"), f"{name} missing frontmatter"
        assert f"name: {name}" in content


def test_creates_new_skill_files(workspace: Path) -> None:
    run_init(workspace)
    for name in ("odoo-setup", "odoo-data", "odoo-report"):
        path = workspace / ".claude" / "skills" / name / "SKILL.md"
        assert path.exists(), f"Skill {name} not created"
        content = path.read_text()
        assert len(content) > 100
        assert "---" in content


def test_total_file_count(workspace: Path) -> None:
    """run_init should now create 18 files (11 old + 4 agents + 3 new skills)."""
    results = run_init(workspace)
    assert len(results) == 18


def test_update_overwrites_agent_files(workspace: Path) -> None:
    run_init(workspace)
    # Modify an agent file
    agent = workspace / ".claude" / "agents" / "odoo-explorer.md"
    agent.write_text("custom content")
    results = run_init(workspace, update=True)
    status_map = {p: s for p, s in results}
    assert status_map[str(agent)] == "updated"
    assert "custom content" not in agent.read_text()


def test_update_overwrites_new_skills(workspace: Path) -> None:
    run_init(workspace)
    results = run_init(workspace, update=True)
    status_map = {p: s for p, s in results}
    for name in ("odoo-setup", "odoo-data", "odoo-report"):
        key = str(workspace / ".claude" / "skills" / name / "SKILL.md")
        assert status_map[key] == "updated"
```

**Step 2: Run tests to verify they fail**

Run: `uv run python -m pytest tests/test_init.py -v -k "agent or new_skill or total_file_count"`
Expected: FAIL — agents not created, file count is 11 not 18

**Step 3: Update `_copy_skills` to include new skills**

In `src/odooforge/init.py`, change line 152 from:
```python
    for name in ("odoo-brainstorm", "odoo-architect", "odoo-debug"):
```
to:
```python
    for name in ("odoo-brainstorm", "odoo-architect", "odoo-debug",
                 "odoo-setup", "odoo-data", "odoo-report"):
```

**Step 4: Add `_copy_agents` function**

After the `_copy_skills` function (after line 158), add:

```python
def _copy_agents(target: Path, results: list[Result], *, update: bool = False) -> None:
    agents_src = _pkg_data() / "agents"
    for name in ("odoo-explorer", "odoo-executor", "odoo-reviewer", "odoo-analyst"):
        _copy_file(
            agents_src / f"{name}.md",
            target / ".claude" / "agents" / f"{name}.md",
            results,
            update=update,
        )
```

**Step 5: Call `_copy_agents` from `run_init`**

In `run_init`, add the call after `_copy_skills`:

```python
    _copy_skills(target, results, update=update)
    _copy_agents(target, results, update=update)  # NEW
    _create_claude_md(target, results, update=update)
```

**Step 6: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_init.py -v`
Expected: ALL PASS

**Step 7: Commit**

```bash
git add src/odooforge/init.py tests/test_init.py
git commit -m "feat: scaffold agents and new skills in odooforge init"
```

---

### Task 9: Update existing tests for new file count

**Files:**
- Modify: `tests/test_init.py`

**Step 1: Update `test_creates_all_expected_files`**

The `expected` set needs the 4 agent files and 3 new skill files. Update the set and also update `test_run_init_returns_results` to check for 18 files instead of 11.

In `test_creates_all_expected_files`, add to the `expected` set:
```python
        str(workspace / ".claude" / "skills" / "odoo-setup" / "SKILL.md"),
        str(workspace / ".claude" / "skills" / "odoo-data" / "SKILL.md"),
        str(workspace / ".claude" / "skills" / "odoo-report" / "SKILL.md"),
        str(workspace / ".claude" / "agents" / "odoo-explorer.md"),
        str(workspace / ".claude" / "agents" / "odoo-executor.md"),
        str(workspace / ".claude" / "agents" / "odoo-reviewer.md"),
        str(workspace / ".claude" / "agents" / "odoo-analyst.md"),
```

In `test_run_init_returns_results`, change:
```python
    assert len(results) == 18  # total files (was 11)
```

In `test_skill_files_have_content`, update the tuple:
```python
    for name in ("odoo-brainstorm", "odoo-architect", "odoo-debug",
                 "odoo-setup", "odoo-data", "odoo-report"):
```

In `test_update_overwrites_template_files`, add assertions for new files:
```python
    assert status_map[str(workspace / ".claude" / "skills" / "odoo-setup" / "SKILL.md")] == "updated"
    assert status_map[str(workspace / ".claude" / "skills" / "odoo-data" / "SKILL.md")] == "updated"
    assert status_map[str(workspace / ".claude" / "skills" / "odoo-report" / "SKILL.md")] == "updated"
    assert status_map[str(workspace / ".claude" / "agents" / "odoo-explorer.md")] == "updated"
    assert status_map[str(workspace / ".claude" / "agents" / "odoo-executor.md")] == "updated"
    assert status_map[str(workspace / ".claude" / "agents" / "odoo-reviewer.md")] == "updated"
    assert status_map[str(workspace / ".claude" / "agents" / "odoo-analyst.md")] == "updated"
```

**Step 2: Run all tests**

Run: `uv run python -m pytest tests/test_init.py -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add tests/test_init.py
git commit -m "test: update init tests for agents and new skills"
```

---

### Task 10: Update CLAUDE.md template and workspace CLAUDE.md

**Files:**
- Modify: `src/odooforge/init.py` (`_CLAUDE_MD` template)
- Modify: `CLAUDE.md` (repo root — if it exists and has an agents/skills section)

**Step 1: Update `_CLAUDE_MD` in init.py**

Add agents section to the skills section:

```python
## Skills

The `.claude/skills/` directory contains Claude Code skills for guided workflows:
- **/odoo-brainstorm** — Explore Odoo customization ideas
- **/odoo-architect** — Design data models with best practices
- **/odoo-debug** — Diagnose and fix Odoo issues
- **/odoo-setup** — Full business deployment from natural language
- **/odoo-data** — Import, create, and manage business data
- **/odoo-report** — Build dashboards and analyze business data

## Agents

The `.claude/agents/` directory contains specialist subagents:
- **odoo-explorer** — Read-only instance scout (gathers state before planning)
- **odoo-executor** — Plan execution engine (with snapshot safety)
- **odoo-reviewer** — Post-execution validator (checks for regressions)
- **odoo-analyst** — Business data analyst (queries and insights)
```

**Step 2: Run tests**

Run: `uv run python -m pytest tests/test_init.py::test_claude_md_content -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/odooforge/init.py
git commit -m "feat: update CLAUDE.md template with agents and new skills"
```

---

### Task 11: Copy agents and new skills into repo's own .claude/

**Files:**
- Create: `.claude/skills/odoo-setup/SKILL.md` (copy from data)
- Create: `.claude/skills/odoo-data/SKILL.md` (copy from data)
- Create: `.claude/skills/odoo-report/SKILL.md` (copy from data)
- Create: `.claude/agents/odoo-explorer.md` (copy from data)
- Create: `.claude/agents/odoo-executor.md` (copy from data)
- Create: `.claude/agents/odoo-reviewer.md` (copy from data)
- Create: `.claude/agents/odoo-analyst.md` (copy from data)

**Step 1: Copy the files**

```bash
# Skills
for name in odoo-setup odoo-data odoo-report; do
  mkdir -p .claude/skills/$name
  cp src/odooforge/data/skills/$name/SKILL.md .claude/skills/$name/SKILL.md
done

# Agents
mkdir -p .claude/agents
for name in odoo-explorer odoo-executor odoo-reviewer odoo-analyst; do
  cp src/odooforge/data/agents/$name.md .claude/agents/$name.md
done
```

**Step 2: Verify**

Run: `ls -la .claude/skills/ .claude/agents/`
Expected: 6 skill directories, 4 agent files

**Step 3: Commit**

```bash
git add .claude/skills/ .claude/agents/
git commit -m "feat: add new skills and agents to repo workspace"
```

---

### Task 12: Bump version, update CHANGELOG, run full test suite

**Files:**
- Modify: `pyproject.toml:3` (version)
- Modify: `CHANGELOG.md` (new entry)

**Step 1: Bump version to 0.3.0 in pyproject.toml**

Change `version = "0.2.2"` to `version = "0.3.0"`.

**Step 2: Add CHANGELOG entry**

Prepend after line 7:

```markdown
## [0.3.0] — 2026-02-18

### Added

- **Subagent definitions** (4 specialist agents for Claude Code)
  - `odoo-explorer` — read-only instance scout, gathers state before planning
  - `odoo-executor` — plan execution engine with snapshot safety
  - `odoo-reviewer` — post-execution validator, checks for regressions
  - `odoo-analyst` — business data analyst, queries and insights
- **New skills** (3 additional Claude Code skills, total 6)
  - `/odoo-setup` — full business deployment from natural language
  - `/odoo-data` — import, create, and manage business data
  - `/odoo-report` — build dashboards and analyze business data
- `odooforge init` now scaffolds agents (`.claude/agents/`) alongside skills
- Plugin architecture design document (`docs/plans/2026-02-18-odooforge-plugin-architecture.md`)

### Changed

- Total skills increased from 3 to **6**
- Total scaffolded files increased from 11 to **18**
- Test suite expanded
```

**Step 3: Run full test suite**

Run: `uv run python -m pytest tests/ -q`
Expected: ALL PASS

**Step 4: Commit, tag, push**

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to v0.3.0"
git tag v0.3.0
git push && git push --tags
```

---

## Verification

After all tasks, run:

```bash
# All tests pass
uv run python -m pytest tests/ -q

# Init creates 18 files
uv run python -c "from odooforge.init import run_init; import tempfile; from pathlib import Path; t=Path(tempfile.mkdtemp()); r=run_init(t); print(f'{len(r)} files'); assert len(r)==18"

# Agent files have frontmatter
for f in src/odooforge/data/agents/*.md; do head -2 "$f"; echo; done

# Skill files have frontmatter
for f in src/odooforge/data/skills/*/SKILL.md; do head -2 "$f"; echo; done
```
