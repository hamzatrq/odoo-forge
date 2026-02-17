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
├── CLAUDE.md                  # AI assistant context
├── .env                       # Connection settings (edit this!)
├── skills/                    # Claude Code skills
│   ├── odoo-brainstorm.md
│   ├── odoo-architect.md
│   └── odoo-debug.md
├── docker/
│   ├── docker-compose.yml     # Odoo 18 + PostgreSQL 17
│   └── odoo.conf
├── addons/                    # Your custom Odoo modules
├── .cursor/mcp.json           # Cursor MCP config (auto-configured)
├── .windsurf/mcp.json         # Windsurf MCP config (auto-configured)
└── .gitignore
```

### Updating After Upgrade

After upgrading OdooForge (`pip install --upgrade odooforge`), update your workspace template files:

```bash
odooforge init --update
```

This overwrites skills, configs, and Docker files with the latest versions. Your `.env` is **never** overwritten.

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

No extra config needed — `odooforge init` creates the workspace `CLAUDE.md` and skills automatically. Add the MCP server to your Claude Code config:

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

### 2. Create a database

```
Create a new database called "myshop" with demo data
```

### 3. Install modules

```
Install the Sales, CRM, and Inventory modules
```

### 4. Create records

```
Create a contact named "Acme Corp" with email "info@acme.com"
```

### 5. Try a recipe

```
Show me the available recipes, then run the ecommerce recipe in dry-run mode
```

## Safety Tips

- **Always create snapshots** before making major changes (module installs, schema changes)
- **Use dry-run mode** for recipes and imports before executing
- **Destructive operations** (delete, drop, uninstall) require `confirm=true` — the AI will ask for confirmation

## Next Steps

- [Configuration Reference](configuration.md) — All environment variables and Docker setup
- [Tool Reference](tools/overview.md) — Complete documentation for all 79 tools
- [Architecture](architecture.md) — How OdooForge works under the hood
- [Industry Recipes](recipes.md) — Pre-built setups for common business types
