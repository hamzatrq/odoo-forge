# Getting Started

This guide will help you install OdooForge, set up a workspace, and start managing Odoo 18 with AI assistants.

## Prerequisites

- **Python 3.11+**
- **Docker** and **Docker Compose** (for hosting Odoo)
- An MCP-compatible AI client (**Claude Code**, **Claude Desktop**, **Cursor**, **Windsurf**, or any MCP client)

## Installation

```bash
pip install odooforge
```

Or run directly with uvx (no install needed):

```bash
uvx odooforge
```

## Initialize a Workspace

Create a new project directory and run `odooforge init`:

```bash
mkdir my-odoo-project && cd my-odoo-project
odooforge init
```

This scaffolds everything you need:

```
.
├── CLAUDE.md                     # AI assistant context
├── .env                          # Connection settings (edit this!)
├── .claude/
│   ├── skills/                   # 6 Claude Code skills
│   │   ├── odoo-brainstorm/SKILL.md    # /odoo-brainstorm
│   │   ├── odoo-architect/SKILL.md     # /odoo-architect
│   │   ├── odoo-debug/SKILL.md         # /odoo-debug
│   │   ├── odoo-setup/SKILL.md         # /odoo-setup
│   │   ├── odoo-data/SKILL.md          # /odoo-data
│   │   └── odoo-report/SKILL.md        # /odoo-report
│   └── agents/                   # 4 specialist subagents
│       ├── odoo-explorer.md      # Read-only instance scout
│       ├── odoo-executor.md      # Plan execution engine
│       ├── odoo-reviewer.md      # Post-execution validator
│       └── odoo-analyst.md       # Business data analyst
├── docker/
│   ├── docker-compose.yml        # Odoo 18 + PostgreSQL 17
│   └── odoo.conf
├── addons/                       # Your custom Odoo modules
├── .cursor/mcp.json              # Cursor MCP config (auto-configured)
├── .windsurf/mcp.json            # Windsurf MCP config (auto-configured)
└── .gitignore
```

### Updating After Upgrade

After upgrading OdooForge (`pip install --upgrade odooforge`), update your workspace template files:

```bash
odooforge init --update
```

This overwrites skills, agents, configs, and Docker files with the latest versions. Your `.env` is **never** overwritten.

## Start Odoo

Edit `.env` with your connection details, then start the included Docker stack:

```bash
cd docker && docker compose up -d
```

This starts:
- **Odoo 18** on `http://localhost:8069`
- **PostgreSQL 17** on `localhost:5432`

Verify Odoo is running:
```bash
curl http://localhost:8069/web/health
```

## Connect Your MCP Client

The `odooforge init` command already creates MCP configs for **Cursor** and **Windsurf**. For other clients:

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "odooforge": {
      "command": "uvx",
      "args": ["odooforge"],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DEFAULT_DB": "odoo",
        "ODOO_ADMIN_USER": "admin",
        "ODOO_ADMIN_PASSWORD": "admin",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "odoo",
        "POSTGRES_PASSWORD": "odoo"
      }
    }
  }
}
```

### Claude Code

No extra config needed — `odooforge init` creates the workspace `CLAUDE.md`, skills, and agents automatically. Add the MCP server to your Claude Code config:

```bash
claude mcp add odooforge -- uvx odooforge
```

### Environment Variables

The `.env` file created by `odooforge init` contains all settings (see [Configuration](configuration.md) for details):

```bash
ODOO_URL=http://localhost:8069
ODOO_DEFAULT_DB=odoo
ODOO_ADMIN_USER=admin
ODOO_ADMIN_PASSWORD=admin
```

## First Steps

Once connected, try these prompts with your AI assistant:

### 1. Check system health

```
Run a health check on my Odoo instance
```

This calls `odoo_diagnostics_health_check` and verifies Docker, database, authentication, and module status.

### 2. Set up a business

```
I run a small bakery with 2 locations. Set up my Odoo for me.
```

In Claude Code, this activates the `/odoo-setup` skill, which guides the full Discover → Plan → Build flow.

### 3. Install modules

```
Install the Sales, CRM, and Inventory modules
```

### 4. Import data

```
I have a CSV of products to import — help me get them into Odoo
```

The `/odoo-data` skill guides the import workflow with previews and validation.

### 5. Analyze your business

```
How are my sales doing this month? Show me a breakdown by product.
```

The `/odoo-report` skill dispatches the `odoo-analyst` agent for SQL-powered insights.

### 6. Fix issues

```
I'm getting an error when creating invoices — can you help debug it?
```

The `/odoo-debug` skill runs diagnostics, reads logs, and suggests fixes.

## Skills & Agents

### Skills (Claude Code)

Skills are slash commands that guide Claude through structured workflows:

| Skill | When to Use |
|-------|-------------|
| `/odoo-brainstorm` | Exploring what Odoo can do for your business |
| `/odoo-architect` | Designing custom data models |
| `/odoo-setup` | Deploying Odoo for a business from scratch |
| `/odoo-data` | Importing data, creating records, migrating |
| `/odoo-report` | Building dashboards, analyzing data |
| `/odoo-debug` | Diagnosing and fixing issues |

### Agents (Claude Code)

Agents are specialists that Claude dispatches for focused work:

| Agent | What It Does |
|-------|-------------|
| `odoo-explorer` | Scouts your instance (read-only) — installed modules, schema, customizations |
| `odoo-executor` | Executes plans step-by-step with automatic snapshots |
| `odoo-reviewer` | Validates results after execution, checks for regressions |
| `odoo-analyst` | Runs SQL queries and generates business insights |

Agents have constrained tool access — read-only agents can't modify your instance.

## Safety Tips

- **Always create snapshots** before making major changes (module installs, schema changes)
- **Use dry-run mode** for recipes and imports before executing
- **Destructive operations** (delete, drop, uninstall) require `confirm=true` — the AI will ask for confirmation
- **The executor agent** creates snapshots automatically before each mutation

## Next Steps

- [Configuration Reference](configuration.md) — All environment variables and Docker setup
- [Tool Reference](tools/overview.md) — Complete documentation for all 79 tools
- [Architecture](architecture.md) — How OdooForge works under the hood
- [Industry Recipes](recipes.md) — Pre-built setups for common business types
