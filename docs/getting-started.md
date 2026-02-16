# Getting Started

This guide will help you install OdooForge, connect it to an AI assistant, and start managing Odoo 18 with natural language.

## Prerequisites

- **Python 3.11+**
- **Docker** and **Docker Compose** (for hosting Odoo)
- An MCP-compatible AI client (**Claude Desktop**, **Cursor**, or any MCP client)

## Installation

### Option 1: pip install (recommended)

```bash
pip install odooforge
```

### Option 2: Run directly with uvx

```bash
uvx odooforge
```

### Option 3: From source

```bash
git clone https://github.com/hamzatrq/odoo-forge.git
cd odoo-forge
uv sync
```

## Starting Odoo

OdooForge includes a Docker Compose file with Odoo 18 and PostgreSQL 17:

```bash
# From the project directory
docker compose -f docker/docker-compose.yml up -d
```

This starts:
- **Odoo 18** on `http://localhost:8069`
- **PostgreSQL 17** on `localhost:5432`

Verify Odoo is running:
```bash
curl http://localhost:8069/web/health
```

## Connect Your MCP Client

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
        "POSTGRES_USER": "odoo",
        "POSTGRES_PASSWORD": "odoo"
      }
    }
  }
}
```

### Cursor

Add to your Cursor MCP settings:

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
        "ODOO_ADMIN_PASSWORD": "admin"
      }
    }
  }
}
```

### Environment Variables

Create a `.env` file in your working directory (see [Configuration](configuration.md) for all options):

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
- [Tool Reference](tools/overview.md) — Complete documentation for all 71 tools
- [Architecture](architecture.md) — How OdooForge works under the hood
- [Industry Recipes](recipes.md) — Pre-built setups for common business types
